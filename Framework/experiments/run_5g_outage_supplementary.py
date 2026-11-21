"""Run a separate, reproducible 5G-backhaul outage/fallback experiment.

This is deliberately kept separate from the archived 24-configuration primary
matrix. It uses the same traffic/model parameters and the same six algorithms,
but writes to results/supplementary/5g_outage/ so the original primary data are
never overwritten or mixed with this supplementary validation.

Example:
    python experiments/run_5g_outage_supplementary.py --seeds 5
"""
from __future__ import annotations

import argparse
import json
import sys
import gc
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import simpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.algorithms import FixedNB, Fixed5G, LatFirst, EnerFirst, StatTOP, AdapAHP  # noqa: E402
from src.simulation.network import EdgeGateway  # noqa: E402
from src.core.paired_statistics import paired_t_summary  # noqa: E402

DURATION_S = 3600.0
OUTAGE_START_S = 2000.0
OUTAGE_DURATION_S = 30.0
OUTAGE_END_S = OUTAGE_START_S + OUTAGE_DURATION_S
ALGORITHMS = {
    "NB": FixedNB(),
    "5G": Fixed5G(),
    "LAT": LatFirst(),
    "ENG": EnerFirst(),
    "TOP": StatTOP(),
    "AHP": AdapAHP(),
}


def generate_trace(seed: int, rate: float = 2.0, duration: float = DURATION_S, emerg_ratio: float = 0.10):
    rng = np.random.RandomState(seed)
    t = 0.0
    trace = []
    pid = 0
    while t < duration:
        t += float(rng.exponential(1.0 / rate))
        if t > duration:
            break
        emergency = bool(rng.rand() < emerg_ratio)
        trace.append(
            {
                "pid": pid,
                "arr": t,
                "emerg": emergency,
                "payload": 200 if emergency else 50,
                "rel_roll": {"NB": float(rng.rand() * 100), "5G": float(rng.rand() * 100)},
            }
        )
        pid += 1
    return trace


def mean_ci(values: pd.Series) -> tuple[float, float, float]:
    x = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if not len(x):
        return float("nan"), float("nan"), float("nan")
    mean = float(np.mean(x))
    if len(x) < 2:
        return mean, float("nan"), float("nan")
    sample_sd = float(np.std(x, ddof=1))
    if not np.isfinite(sample_sd) or sample_sd == 0.0:
        return mean, float("nan"), float("nan")
    half = float(stats.t.ppf(0.975, len(x) - 1) * stats.sem(x))
    return mean, mean - half, mean + half


def run_one(seed: int, algo_name: str, algo) -> dict:
    trace = generate_trace(seed)
    events = [{"type": "5G_OUTAGE", "start": OUTAGE_START_S, "dur": OUTAGE_DURATION_S}]
    env = simpy.Environment()
    gateway = EdgeGateway(env, algo, [dict(packet) for packet in trace], events)
    env.run(until=DURATION_S)
    gateway.end_of_simulation_sweep()
    frame = pd.DataFrame(list(gateway.registry.values()))

    generated = len(frame)
    delivered = frame[frame["status"] == "DELIVERED"]
    emergency_all = frame[frame["emerg"] == True]  # noqa: E712
    emergency_delivered = delivered[delivered["emerg"] == True]  # noqa: E712
    in_outage = frame[(frame["arr"] >= OUTAGE_START_S) & (frame["arr"] < OUTAGE_END_S)]
    selected = frame[frame["sel_net"].notna()] if "sel_net" in frame else frame.iloc[0:0]
    outage_selected = selected[(selected["arr"] >= OUTAGE_START_S) & (selected["arr"] < OUTAGE_END_S)]
    recovery_selected = selected[selected["arr"] >= OUTAGE_END_S]

    terminal_statuses = {
        "DELIVERED", "DROP_QOS", "DROP_OUTAGE", "DROP_RELIABILITY",
        "DROP_QUEUE_OVERFLOW_CPU", "DROP_QUEUE_OVERFLOW_BH",
    }
    in_flight = frame[frame["status"].astype(str).str.startswith("IN_FLIGHT_")]
    dropped = frame[frame["status"].isin(terminal_statuses - {"DELIVERED"})]
    assert generated == len(delivered) + len(dropped) + len(in_flight), "Packet accounting mismatch."

    return {
        "Scenario": "K_5G_OUTAGE_SUPPLEMENTARY",
        "Algorithm": algo_name,
        "Seed": seed,
        "Generated": generated,
        "Delivered": len(delivered),
        "PDR": len(delivered) / generated if generated else float("nan"),
        "Emergency_PDR": len(emergency_delivered) / len(emergency_all) if len(emergency_all) else float("nan"),
        "Mean_Latency_s": delivered["lat_actual"].mean() if len(delivered) else float("nan"),
        "P95_Latency_s": delivered["lat_actual"].quantile(0.95) if len(delivered) else float("nan"),
        "Total_Energy_J": gateway.cpu_energy_consumed + gateway.a1.energy_setup_tx_j + gateway.a2.energy_setup_tx_j,
        "NB_Selections": int((selected.get("sel_net", pd.Series(dtype=float)) == 0).sum()),
        "5G_Selections": int((selected.get("sel_net", pd.Series(dtype=float)) == 1).sum()),
        "NB_Selections_During_5G_Outage": int((outage_selected.get("sel_net", pd.Series(dtype=float)) == 0).sum()),
        "5G_Selections_During_5G_Outage": int((outage_selected.get("sel_net", pd.Series(dtype=float)) == 1).sum()),
        "5G_Selections_After_Recovery": int((recovery_selected.get("sel_net", pd.Series(dtype=float)) == 1).sum()),
        "Switches": int(gateway.switches),
        "QoS_Drops": int((frame["status"] == "DROP_QOS").sum()),
        "Outage_Drops": int((frame["status"] == "DROP_OUTAGE").sum()),
        "Reliability_Drops": int((frame["status"] == "DROP_RELIABILITY").sum()),
        "In_Flight_At_Horizon": int(len(in_flight)),
        "Packets_Arriving_During_Outage": int(len(in_outage)),
    }


def summarize(raw: pd.DataFrame, out_dir: Path) -> None:
    metrics = [
        "PDR", "Emergency_PDR", "Mean_Latency_s", "P95_Latency_s", "Total_Energy_J",
        "NB_Selections_During_5G_Outage", "5G_Selections_During_5G_Outage",
        "5G_Selections_After_Recovery", "Switches", "QoS_Drops", "Outage_Drops",
    ]
    rows = []
    for algorithm, group in raw.groupby("Algorithm", sort=False):
        row = {"Algorithm": algorithm, "Seeds": int(group["Seed"].nunique())}
        for metric in metrics:
            mean, low, high = mean_ci(group[metric])
            row[f"{metric}_Mean"] = mean
            row[f"{metric}_CI95_Lower"] = low
            row[f"{metric}_CI95_Upper"] = high
            row[f"{metric}_SD"] = float(group[metric].std(ddof=1)) if group[metric].notna().sum() > 1 else float("nan")
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(out_dir / "summary.csv", index=False)

    # Paired comparisons against the non-failing Fixed-5G baseline.
    baseline = raw[raw["Algorithm"] == "5G"].set_index("Seed")
    paired_rows = []
    for algorithm in ["NB", "LAT", "ENG", "TOP", "AHP"]:
        candidate = raw[raw["Algorithm"] == algorithm].set_index("Seed")
        merged = candidate.join(baseline, lsuffix="_candidate", rsuffix="_fixed5g", how="inner")
        for metric in ["PDR", "Mean_Latency_s", "Total_Energy_J"]:
            delta = (merged[f"{metric}_candidate"] - merged[f"{metric}_fixed5g"]).dropna()
            comparison = paired_t_summary(delta.to_numpy(dtype=float), alpha=0.05)
            n = int(comparison["Valid_Pairs"])
            mean_delta = float(comparison["Mean_Difference"])
            paired_rows.append({
                "Algorithm": algorithm,
                "Metric": metric,
                "Valid_Pairs": n,
                "Mean_Difference_vs_Fixed5G": mean_delta,
                "Difference_SD": comparison["Difference_SD"],
                "Observed_Difference_Min": comparison["Observed_Difference_Min"],
                "Observed_Difference_Max": comparison["Observed_Difference_Max"],
                "CI95_Lower": comparison["CI_Lower"],
                "CI95_Upper": comparison["CI_Upper"],
                "Paired_Cohens_dz": comparison["Cohens_dz"],
                "T_Statistic": comparison["T_Statistic"],
                "P_Value_Unadjusted": comparison["P_Value"],
                "Wilcoxon_P_Value": comparison["Wilcoxon_P_Value"],
                "Wilcoxon_Method": comparison["Wilcoxon_Method"],
                "Shapiro_W": comparison["Shapiro_W"],
                "Shapiro_P": comparison["Shapiro_P"],
                "Inference_Status": comparison["Inference_Status"],
            })
    paired = pd.DataFrame(paired_rows)
    paired["P_Value_BH_FDR"] = np.nan
    paired["Wilcoxon_P_Value_BH_FDR"] = np.nan
    for metric, indices in paired.groupby("Metric").groups.items():
        for source_column, target_column in [
            ("P_Value_Unadjusted", "P_Value_BH_FDR"),
            ("Wilcoxon_P_Value", "Wilcoxon_P_Value_BH_FDR"),
        ]:
            family = paired.loc[indices, source_column]
            valid = family.notna()
            if valid.any():
                order = np.argsort(family.loc[valid].to_numpy(dtype=float))
                p_sorted = family.loc[valid].to_numpy(dtype=float)[order]
                m = len(p_sorted)
                q_sorted = np.minimum.accumulate((p_sorted * m / np.arange(1, m + 1))[::-1])[::-1]
                q_sorted = np.clip(q_sorted, 0.0, 1.0)
                q_original_order = np.empty_like(q_sorted)
                q_original_order[order] = q_sorted
                paired.loc[family.loc[valid].index, target_column] = q_original_order
    paired.to_csv(out_dir / "paired_vs_fixed5g.csv", index=False)

    selection_rows = []
    for algorithm, group in raw.groupby("Algorithm", sort=False):
        selection_rows.append({
            "Algorithm": algorithm,
            "NB_Selections_During_5G_Outage_Mean": group["NB_Selections_During_5G_Outage"].mean(),
            "5G_Selections_During_5G_Outage_Mean": group["5G_Selections_During_5G_Outage"].mean(),
            "5G_Selections_After_Recovery_Mean": group["5G_Selections_After_Recovery"].mean(),
            "Switches_Mean": group["Switches"].mean(),
        })
    pd.DataFrame(selection_rows).to_csv(out_dir / "selection_summary.csv", index=False)

    # Publication-ready supplementary diagnostic figure (not a replacement for primary figures).
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ordered = ["NB", "5G", "LAT", "ENG", "TOP", "AHP"]
    summary_plot = summary.set_index("Algorithm").reindex(ordered).reset_index()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    axes[0].bar(summary_plot["Algorithm"], summary_plot["PDR_Mean"] * 100)
    axes[0].set_title("PDR over full run")
    axes[0].set_ylabel("Delivered packets (%)")
    axes[0].set_ylim(0, 100)
    axes[1].bar(summary_plot["Algorithm"], summary_plot["NB_Selections_During_5G_Outage_Mean"])
    axes[1].set_title("NB-IoT selections during outage")
    axes[1].set_ylabel("Mean selections per seed")
    axes[2].bar(summary_plot["Algorithm"], summary_plot["5G_Selections_After_Recovery_Mean"])
    axes[2].set_title("5G selections after recovery")
    axes[2].set_ylabel("Mean selections per seed")
    fig.suptitle("Supplementary 5G backhaul outage and fallback evaluation")
    fig.tight_layout()
    figure_dir = ROOT / "results" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_dir / "08_5g_outage_failover.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    import subprocess

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=5, help="Number of paired seeds (default: 5; pilot-size supplementary evaluation).")
    parser.add_argument("--start-seed", type=int, default=1000)
    parser.add_argument("--worker-seed", type=int, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.seeds < 2:
        raise SystemExit("Use at least 2 seeds for a supplementary descriptive comparison.")

    out_dir = ROOT / "results" / "supplementary" / "5g_outage"
    out_dir.mkdir(parents=True, exist_ok=True)
    algorithm_factories = {
        "NB": FixedNB, "5G": Fixed5G, "LAT": LatFirst,
        "ENG": EnerFirst, "TOP": StatTOP, "AHP": AdapAHP,
    }

    # Worker mode: execute one paired seed in a fresh Python process. Isolating
    # seeds prevents long-lived SimPy event/process object graphs from
    # accumulating across many independent environments.
    if args.worker_seed is not None:
        seed = int(args.worker_seed)
        worker_rows = []
        for name, factory in algorithm_factories.items():
            print(f"  seed {seed}: {name}", flush=True)
            worker_rows.append(run_one(seed, name, factory()))
        pd.DataFrame(worker_rows).to_csv(out_dir / f"seed_{seed}.csv", index=False)
        return

    seeds = list(range(args.start_seed, args.start_seed + args.seeds))
    for index, seed in enumerate(seeds, start=1):
        seed_file = out_dir / f"seed_{seed}.csv"
        if seed_file.exists():
            try:
                existing = pd.read_csv(seed_file)
                if set(existing["Algorithm"]) == set(algorithm_factories) and len(existing) == len(algorithm_factories):
                    print(f"Seed {index}/{len(seeds)} already complete: {seed}", flush=True)
                    continue
            except Exception:
                pass
        print(f"Running outage supplementary seed {index}/{len(seeds)}: {seed}", flush=True)
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker-seed", str(seed)],
            cwd=str(ROOT),
            check=True,
        )

    seed_frames = []
    for seed in seeds:
        seed_file = out_dir / f"seed_{seed}.csv"
        if not seed_file.exists():
            raise RuntimeError(f"Missing completed seed checkpoint: {seed_file}")
        frame = pd.read_csv(seed_file)
        if len(frame) != len(algorithm_factories) or frame["Algorithm"].duplicated().any():
            raise RuntimeError(f"Invalid seed checkpoint: {seed_file}")
        seed_frames.append(frame)
    raw = pd.concat(seed_frames, ignore_index=True)
    expected = args.seeds * len(algorithm_factories)
    if len(raw) != expected or raw.duplicated(["Algorithm", "Seed"]).any():
        raise RuntimeError(f"Supplementary outage matrix incomplete/duplicated: expected {expected}, got {len(raw)}")

    raw.to_csv(out_dir / "raw_metrics.csv", index=False)
    summarize(raw, out_dir)
    metadata = {
        "scenario": "K_5G_OUTAGE_SUPPLEMENTARY",
        "duration_s": DURATION_S,
        "outage_start_s": OUTAGE_START_S,
        "outage_duration_s": OUTAGE_DURATION_S,
        "seeds": seeds,
        "algorithms": list(algorithm_factories),
        "rows": len(raw),
        "primary_24_scenario_matrix_modified": False,
        "seed_execution": "one independent Python process per seed",
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed {len(raw)} supplementary simulation runs.", flush=True)


if __name__ == "__main__":
    main()
