"""Short paired SimPy validation for the two-timescale controller.

This is a targeted smoke experiment, not a replacement for the archived
30-seed primary experiment and not a statistically powered evaluation.
Outputs go only to results/supplementary/two_timescale/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import simpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.algorithms import AdapAHP, TwoTimescale
from src.core.two_timescale import TwoTimescaleConfig
from src.simulation.network import EdgeGateway

OUT = ROOT / "results" / "supplementary" / "two_timescale"
OUT.mkdir(parents=True, exist_ok=True)


def generate_trace(seed: int, rate: float, duration: float, emergency_ratio: float):
    rng = np.random.default_rng(seed)
    t = 0.0
    trace = []
    pid = 0
    while True:
        t += float(rng.exponential(1.0 / rate))
        if t > duration:
            break
        emergency = bool(rng.random() < emergency_ratio)
        trace.append({
            "pid": pid,
            "arr": t,
            "emerg": emergency,
            "payload": 200 if emergency else 50,
            "rel_roll": {"NB": float(rng.random() * 100), "5G": float(rng.random() * 100)},
        })
        pid += 1
    return trace


def run_one(trace, events, algorithm, seed, duration, rate):
    env = simpy.Environment()
    gateway = EdgeGateway(env, algorithm, [dict(p) for p in trace], list(events))
    env.run(until=duration)
    gateway.end_of_simulation_sweep()
    frame = pd.DataFrame(list(gateway.registry.values()))
    delivered = frame[frame["status"] == "DELIVERED"]
    emergency = frame[frame["emerg"].astype(bool)]
    emergency_delivered = delivered[delivered["emerg"].astype(bool)]
    decisions = gateway.decision_log
    mode_counts = Counter(d.get("decision_mode", "unknown") for d in decisions)
    metrics = {
        "Seed": seed,
        "Algorithm": "TWO_TIMESCALE" if isinstance(algorithm, TwoTimescale) else "ADAPTIVE_AHP_TOPSIS",
        "Duration_s": duration,
        "Offered_Load_pps": rate,
        "Generated": int(len(frame)),
        "Delivered": int(len(delivered)),
        "PDR": float(len(delivered) / len(frame)) if len(frame) else 0.0,
        "Emergency_Generated": int(len(emergency)),
        "Emergency_Delivered": int(len(emergency_delivered)),
        "Emergency_PDR": float(len(emergency_delivered) / len(emergency)) if len(emergency) else None,
        "Mean_Latency_s": float(delivered["lat_actual"].mean()) if len(delivered) else None,
        "P95_Latency_s": float(delivered["lat_actual"].quantile(0.95)) if len(delivered) else None,
        "Total_Modelled_Energy_J": float(
            gateway.cpu_energy_consumed + gateway.a1.energy_setup_tx_j + gateway.a2.energy_setup_tx_j
        ),
        "NB_Selections": int((frame.get("sel_net", pd.Series(index=frame.index, dtype=float)) == 0).sum()),
        "5G_Selections": int((frame.get("sel_net", pd.Series(index=frame.index, dtype=float)) == 1).sum()),
        "Packet_Selection_Changes": int(gateway.switches),
        "Persistent_Controller_Switches": int(getattr(getattr(algorithm, "controller", None), "persistent_switches", 0)),
        "Packet_QoS_Overrides": int(getattr(getattr(algorithm, "controller", None), "packet_overrides", 0)),
        "Forced_Fallbacks": int(getattr(getattr(algorithm, "controller", None), "forced_fallbacks", 0)),
        "Decision_Mode_Counts": json.dumps(dict(mode_counts), sort_keys=True),
        "Mean_Decision_Time_us": float(frame["algo_time_us"].dropna().mean()) if frame["algo_time_us"].notna().any() else None,
        "QoS_Drops": int((frame["status"] == "DROP_QOS").sum()),
        "Outage_Drops": int((frame["status"] == "DROP_OUTAGE").sum()),
        "Reliability_Drops": int((frame["status"] == "DROP_RELIABILITY").sum()),
    }
    decision_rows = []
    for record in decisions:
        decision_rows.append({"Seed": seed, **record})
    return metrics, decision_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=120.0)
    parser.add_argument("--rate-pps", type=float, default=2.0)
    parser.add_argument("--emergency-ratio", type=float, default=0.10)
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in range(1000, 1030)))
    parser.add_argument("--output-dir", type=Path, default=OUT, help="Directory for targeted result CSVs and metadata")
    parser.add_argument("--outage-start-s", type=float, default=40.0)
    parser.add_argument("--outage-duration-s", type=float, default=20.0)
    args = parser.parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    if not seeds:
        raise SystemExit("At least one seed is required")
    if args.duration_s <= 10 or args.rate_pps <= 0:
        raise SystemExit("Duration must exceed 10 seconds and rate must be positive")
    if args.outage_start_s < 0 or args.outage_start_s + args.outage_duration_s >= args.duration_s:
        raise SystemExit("Outage must start and finish inside the simulation horizon")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    all_decisions = []
    wall_start = time.perf_counter()
    for seed in seeds:
        trace = generate_trace(seed, args.rate_pps, args.duration_s, args.emergency_ratio)
        events = [{"type": "5G_OUTAGE", "start": args.outage_start_s, "dur": args.outage_duration_s}]
        algorithms = [
            AdapAHP(),
            TwoTimescale(TwoTimescaleConfig(
                initial_arrival_rate_pps=args.rate_pps,
                arrival_rate_ewma_alpha=0.2,
                maximum_expected_packets=10_000.0,
                minimum_dwell_s=2.0,
                improvement_threshold=0.10,
                minimum_reliability_pct=None,
                # Existing modem model omits idle-tail power; keep it excluded.
                idle_power_w={"NB-IoT": 0.0, "5G NR": 0.0},
                expected_idle_seconds_per_session=0.0,
                switching_energy_j=0.0,
            )),
        ]
        for algo in algorithms:
            metrics, decisions = run_one(trace, events, algo, seed, args.duration_s, args.rate_pps)
            all_metrics.append(metrics)
            all_decisions.extend(decisions)
            print(f"seed={seed} algorithm={metrics['Algorithm']} generated={metrics['Generated']} PDR={metrics['PDR']:.4f}")

    wall_s = time.perf_counter() - wall_start
    metrics_frame = pd.DataFrame(all_metrics)
    decisions_frame = pd.DataFrame(all_decisions)
    metrics_frame.to_csv(output_dir / "targeted_smoke_metrics.csv", index=False)
    decisions_frame.to_csv(output_dir / "targeted_smoke_decisions.csv", index=False)
    metadata = {
        "analysis": "Targeted paired SimPy evaluation of the two-timescale controller",
        "evaluation_classification": "exploratory_targeted_paired_simulation",
        "seed_count": len(seeds),
        "seeds": seeds,
        "duration_s": args.duration_s,
        "offered_load_pps": args.rate_pps,
        "emergency_ratio": args.emergency_ratio,
        "event": {"type": "5G_OUTAGE", "start_s": args.outage_start_s, "duration_s": args.outage_duration_s},
        "wall_runtime_s": wall_s,
        "paired_input_traces": True,
        "historical_results_modified": False,
        "statistical_scope": "Exploratory paired evaluation; one offered load, 120-second horizon and one outage schedule do not establish generalization across operating conditions.",
        "controller_config": {
            "initial_arrival_rate_pps": args.rate_pps,
            "arrival_rate_ewma_alpha": 0.2,
            "maximum_expected_packets": 10000.0,
            "minimum_dwell_s": 2.0,
            "improvement_threshold": 0.10,
            "minimum_reliability_pct": None,
            "idle_power_w": {"NB-IoT": 0.0, "5G NR": 0.0},
            "expected_idle_seconds_per_session": 0.0,
            "switching_energy_j": 0.0,
        },
        "idle_tail_power": "Excluded: the existing model does not define idle modem power.",
        "switching_energy": "Set to zero because no calibrated switching-energy measurement is available.",
    }
    (output_dir / "targeted_smoke_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(metrics_frame)} paired metric rows and {len(decisions_frame)} decision rows.")
    print(f"Wall runtime: {wall_s:.3f} s")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
