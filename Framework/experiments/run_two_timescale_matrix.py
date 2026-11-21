"""Run a bounded paired multi-operating-point SimPy evaluation of TSC.

Each (outage pattern, emergency-share, offered-load, seed) condition creates
one input trace replayed by both AHP-TOPSIS and TSC. Results are checkpointed
after each complete condition. This is not the archived primary experiment.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_two_timescale_smoke import generate_trace, run_one
from src.core.algorithms import AdapAHP, TwoTimescale
from src.core.two_timescale import TwoTimescaleConfig

DEFAULT_OUT = ROOT / "results" / "supplementary" / "two_timescale" / "multi_operating_point"


def build_events(pattern: str, duration_s: float, single_start_s: float, single_duration_s: float):
    """Return sorted, non-overlapping 5G outage events for one condition."""
    if pattern == "none":
        return []
    if pattern == "single":
        return [{"type": "5G_OUTAGE", "start": single_start_s, "dur": single_duration_s}]
    if pattern == "repeated":
        outage_duration = min(single_duration_s / 2.0, duration_s / 12.0)
        starts = [duration_s * 0.20, duration_s * 0.45, duration_s * 0.70]
        events = [{"type": "5G_OUTAGE", "start": start, "dur": outage_duration} for start in starts]
        if any(event["start"] + event["dur"] >= duration_s for event in events):
            raise ValueError("Repeated outage schedule does not fit inside the simulation horizon")
        return events
    raise ValueError(f"Unsupported outage pattern: {pattern}")


def parse_float_list(raw: str, name: str) -> list[float]:
    try:
        values = [float(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be comma-separated numbers") from exc
    if not values:
        raise argparse.ArgumentTypeError(f"{name} must contain at least one number")
    return values


def make_algorithms(rate: float):
    return [
        AdapAHP(),
        TwoTimescale(TwoTimescaleConfig(
            initial_arrival_rate_pps=rate,
            arrival_rate_ewma_alpha=0.2,
            maximum_expected_packets=10_000.0,
            minimum_dwell_s=2.0,
            improvement_threshold=0.10,
            minimum_reliability_pct=None,
            idle_power_w={"NB-IoT": 0.0, "5G NR": 0.0},
            expected_idle_seconds_per_session=0.0,
            switching_energy_j=0.0,
        )),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-s", type=float, default=120.0)
    parser.add_argument("--rates-pps", default="0.5,1,2,4,8")
    parser.add_argument("--emergency-ratios", default="0.10,0.25")
    parser.add_argument("--outage-patterns", default="none,single,repeated", help="Comma-separated: none,single,repeated")
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in range(1000, 1030)))
    parser.add_argument("--outage-start-s", type=float, default=40.0)
    parser.add_argument("--outage-duration-s", type=float, default=20.0)
    parser.add_argument("--max-runtime-s", type=float, default=900.0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rates = parse_float_list(args.rates_pps, "rates-pps")
    emergency_ratios = parse_float_list(args.emergency_ratios, "emergency-ratios")
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    outage_patterns = [value.strip().lower() for value in args.outage_patterns.split(",") if value.strip()]
    if not outage_patterns or any(value not in {"none", "single", "repeated"} for value in outage_patterns):
        raise SystemExit("Outage patterns must be selected from none,single,repeated")
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("Seeds must be non-empty and unique")
    if any(rate <= 0 for rate in rates):
        raise SystemExit("All offered loads must be positive")
    if any(not 0 <= ratio < 1 for ratio in emergency_ratios):
        raise SystemExit("Emergency ratios must be in [0, 1)")
    if args.duration_s <= 10:
        raise SystemExit("Duration must exceed 10 seconds")
    if args.outage_start_s < 0 or args.outage_start_s + args.outage_duration_s >= args.duration_s:
        raise SystemExit("Single outage must start and finish inside the simulation horizon")
    if args.max_runtime_s <= 0:
        raise SystemExit("Maximum runtime must be positive")

    total_conditions = len(rates) * len(emergency_ratios) * len(outage_patterns)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_rows: list[dict] = []
    decision_rows: list[dict] = []
    total_start = time.perf_counter()
    complete_conditions = 0
    interrupted_by_budget = False

    for outage_pattern in outage_patterns:
        for emergency_ratio in emergency_ratios:
            for rate in rates:
                condition_id = f"load_{rate:g}_emergency_{emergency_ratio:g}_outage_{outage_pattern}".replace(".", "p")
                condition_start = time.perf_counter()
                events = build_events(outage_pattern, args.duration_s, args.outage_start_s, args.outage_duration_s)
                for seed in seeds:
                    if time.perf_counter() - total_start >= args.max_runtime_s:
                        interrupted_by_budget = True
                        break
                    trace = generate_trace(seed, rate, args.duration_s, emergency_ratio)
                    for algorithm in make_algorithms(rate):
                        metrics, decisions = run_one(trace, events, algorithm, seed, args.duration_s, rate)
                        metrics.update({
                            "Condition_ID": condition_id,
                            "Emergency_Ratio": emergency_ratio,
                            "Outage_Pattern": outage_pattern,
                        })
                        metrics_rows.append(metrics)
                        for decision in decisions:
                            decision_rows.append({
                                "Condition_ID": condition_id,
                                "Offered_Load_pps": rate,
                                "Emergency_Ratio": emergency_ratio,
                                "Outage_Pattern": outage_pattern,
                                **decision,
                            })
                if interrupted_by_budget:
                    break

                complete_conditions += 1
                pd.DataFrame(metrics_rows).to_csv(args.output_dir / "matrix_metrics.csv", index=False)
                pd.DataFrame(decision_rows).to_csv(args.output_dir / "matrix_decisions.csv", index=False)
                state = {
                    "status": "running" if complete_conditions < total_conditions else "completed",
                    "complete_conditions": complete_conditions,
                    "total_conditions": total_conditions,
                    "completed_condition_id": condition_id,
                    "completed_seeds_in_condition": len(seeds),
                    "seed_count_per_condition": len(seeds),
                    "elapsed_wall_seconds": time.perf_counter() - total_start,
                    "last_condition_wall_seconds": time.perf_counter() - condition_start,
                    "historical_results_modified": False,
                }
                (args.output_dir / "matrix_run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
                print(f"Completed {condition_id}: {len(seeds)} paired seeds; elapsed={state['elapsed_wall_seconds']:.2f}s")
            if interrupted_by_budget:
                break
        if interrupted_by_budget:
            break

    wall_s = time.perf_counter() - total_start
    complete = not interrupted_by_budget and complete_conditions == total_conditions
    metadata = {
        "experiment": "paired multi-operating-point TSC evaluation",
        "status": "completed" if complete else "incomplete_runtime_budget",
        "rates_pps": rates,
        "emergency_ratios": emergency_ratios,
        "outage_patterns": outage_patterns,
        "seeds": seeds,
        "duration_s": args.duration_s,
        "single_outage": {"type": "5G_OUTAGE", "start_s": args.outage_start_s, "duration_s": args.outage_duration_s},
        "repeated_outage_schedule": "Three non-overlapping outages at 20%, 45% and 70% of simulation duration; each duration is min(single_outage_duration/2, simulation_duration/12).",
        "complete_conditions": complete_conditions,
        "total_conditions": total_conditions,
        "paired_input_traces": True,
        "max_runtime_s": args.max_runtime_s,
        "wall_runtime_s": wall_s,
        "idle_tail_power": "Excluded; existing model has no calibrated idle modem power.",
        "switching_energy": "Set to zero; no calibrated switching-energy measurement available.",
        "historical_results_modified": False,
    }
    (args.output_dir / "matrix_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Matrix status: {metadata['status']}; completed {complete_conditions}/{total_conditions} conditions in {wall_s:.2f}s")
    print(f"Results: {args.output_dir}")
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
