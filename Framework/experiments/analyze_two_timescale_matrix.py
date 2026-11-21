"""Analyze paired multi-operating-point TSC evaluation output (no SimPy needed)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "results" / "supplementary" / "two_timescale" / "multi_operating_point"
BASELINE = "ADAPTIVE_AHP_TOPSIS"
PROPOSED = "TWO_TIMESCALE"
METRICS = {
    "PDR": "higher",
    "Mean_Latency_s": "lower",
    "P95_Latency_s": "lower",
    "Emergency_PDR": "higher",
    "Total_Modelled_Energy_J": "lower",
    "Mean_Decision_Time_us": "lower",
}


def holm_adjust(values: list[float]) -> list[float]:
    order = np.argsort(values)
    output = np.empty(len(values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * float(values[index])))
        output[index] = running
    return output.tolist()


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    pvals: list[float] = []
    keys = ["Condition_ID", "Offered_Load_pps", "Emergency_Ratio", "Outage_Pattern"]
    for (condition_id, rate, emergency_ratio, outage_pattern), group in frame.groupby(keys, sort=True):
        for metric, direction in METRICS.items():
            pivot = group.pivot(index="Seed", columns="Algorithm", values=metric).sort_index()
            if BASELINE not in pivot or PROPOSED not in pivot:
                raise ValueError(f"Missing algorithm rows in {condition_id} for {metric}")
            diff = pivot[PROPOSED].astype(float) - pivot[BASELINE].astype(float)
            valid = diff.dropna()
            if valid.empty:
                raise ValueError(f"No valid paired observations for {condition_id}/{metric}")
            if np.allclose(valid.to_numpy(), 0):
                statistic, p = 0.0, 1.0
            else:
                result = stats.wilcoxon(valid.to_numpy(), alternative="two-sided", zero_method="wilcox", method="auto")
                statistic, p = float(result.statistic), float(result.pvalue)
            if len(valid) > 1 and valid.std(ddof=1) > 0:
                lo, hi = stats.t.interval(0.95, len(valid)-1, loc=valid.mean(), scale=stats.sem(valid))
            else:
                lo = hi = float(valid.mean())
            rows.append({
                "Condition_ID": condition_id,
                "Offered_Load_pps": float(rate),
                "Emergency_Ratio": float(emergency_ratio),
                "Outage_Pattern": outage_pattern,
                "Metric": metric,
                "Direction": direction,
                "Baseline_Mean": float(pivot[BASELINE].mean()),
                "TSC_Mean": float(pivot[PROPOSED].mean()),
                "Paired_Difference_TSC_Minus_Baseline": float(valid.mean()),
                "Paired_Difference_95CI_Low": float(lo),
                "Paired_Difference_95CI_High": float(hi),
                "Wilcoxon_P_Raw": p,
                "N_Paired_Seeds": int(valid.size),
                "Better_TSC": int(((diff > 0) if direction == "higher" else (diff < 0)).sum()),
                "Tied": int((diff == 0).sum()),
                "Worse_TSC": int(((diff < 0) if direction == "higher" else (diff > 0)).sum()),
            })
            pvals.append(p)
    adjusted = holm_adjust(pvals) if pvals else []
    result_df = pd.DataFrame(rows)
    result_df["Wilcoxon_P_Holm_All_Conditions"] = adjusted
    result_df["Significant_After_Holm_0_05"] = result_df["Wilcoxon_P_Holm_All_Conditions"] < 0.05
    return result_df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output = args.output_dir or args.input_dir
    output.mkdir(parents=True, exist_ok=True)
    metadata_path = args.input_dir / "matrix_metadata.json"
    metrics_path = args.input_dir / "matrix_metrics.csv"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("status") != "completed":
        raise SystemExit("Matrix metadata is not marked completed; do not analyze an incomplete run as final.")
    frame = pd.read_csv(metrics_path)
    if frame.empty:
        raise SystemExit("No matrix metrics available")
    expected_conditions = len(metadata["rates_pps"]) * len(metadata["emergency_ratios"]) * len(metadata["outage_patterns"])
    observed_conditions = frame.Condition_ID.nunique()
    if observed_conditions != expected_conditions:
        raise SystemExit(f"Expected {expected_conditions} conditions, found {observed_conditions}")
    stats_df = analyze(frame)
    stats_df.to_csv(output / "matrix_paired_statistics.csv", index=False)

    agg = frame.groupby(["Condition_ID", "Offered_Load_pps", "Emergency_Ratio", "Outage_Pattern", "Algorithm"], as_index=False).agg(
        Seeds=("Seed", "nunique"), Generated=("Generated", "sum"), Delivered=("Delivered", "sum"),
        Total_Modelled_Energy_J=("Total_Modelled_Energy_J", "sum"),
        Mean_Latency_s=("Mean_Latency_s", "mean"), P95_Latency_s=("P95_Latency_s", "mean"),
        Emergency_PDR=("Emergency_PDR", "mean"), Mean_Decision_Time_us=("Mean_Decision_Time_us", "mean"),
        Persistent_Controller_Switches=("Persistent_Controller_Switches", "sum"),
        Packet_Selection_Changes=("Packet_Selection_Changes", "sum"),
    )
    agg["Pooled_PDR"] = agg["Delivered"] / agg["Generated"]
    agg.to_csv(output / "matrix_aggregate_summary.csv", index=False)

    # Plot paired mean differences at each load, separately for each emergency mix.
    plot_specs = [
        ("Mean_Latency_s", "Latency difference: TSC − AHP-TOPSIS", "seconds"),
        ("PDR", "PDR difference: TSC − AHP-TOPSIS", "fraction"),
        ("Total_Modelled_Energy_J", "Total energy difference: TSC − AHP-TOPSIS", "joules per seed"),
    ]
    for metric, title, unit in plot_specs:
        subset = stats_df[stats_df.Metric == metric]
        fig, ax = plt.subplots(figsize=(7.2, 4.5))
        for (ratio, outage_pattern), group in subset.groupby(["Emergency_Ratio", "Outage_Pattern"]):
            group = group.sort_values("Offered_Load_pps")
            values = group["Paired_Difference_TSC_Minus_Baseline"].to_numpy()
            if metric == "PDR":
                values = values * 100.0
                yunit = "percentage points"
            else:
                yunit = unit
            ax.plot(group["Offered_Load_pps"], values, marker="o", label=f"Emergency {ratio:.0%} / {outage_pattern}")
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlabel("Offered load (packets/s)")
        ax.set_ylabel(f"Paired mean difference ({yunit})")
        ax.set_title(title)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(output / f"matrix_{metric.lower()}_difference.png", dpi=180)
        plt.close(fig)

    lines = [
        "# Multi-Operating-Point TSC Evaluation",
        "",
        f"- Status: `{metadata['status']}`",
        f"- Offered loads: {metadata['rates_pps']} packets/s",
        f"- Emergency shares: {metadata['emergency_ratios']}",
        f"- Outage patterns: {metadata['outage_patterns']}",
        f"- Paired seeds per condition: {len(metadata['seeds'])}",
        f"- Conditions: {observed_conditions}",
        f"- Hypothesis tests after pairing: {stats_df.shape[0]}",
        f"- Wall runtime: {metadata['wall_runtime_s']:.3f} s",
        "- Paired method: same generated input trace for AHP-TOPSIS and TSC within each seed/condition.",
        "- Multiple testing: Holm correction across every metric × operating-condition test in this matrix.",
        "",
        "## Interpretation boundary",
        "",
        "This is a simulation matrix under the configured abstraction, not physical modem validation. The current run excludes idle-tail power and calibrated switching energy. Interpret every condition separately and include losses or regressions; do not select only favourable operating points.",
        "",
        "See `matrix_paired_statistics.csv` for paired differences, confidence intervals, raw and Holm-adjusted p-values, and better/tied/worse seed counts.",
    ]
    (output / "MATRIX_EVALUATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Analyzed {observed_conditions} conditions, {stats_df.shape[0]} paired endpoints.")
    print(f"Outputs: {output}")


if __name__ == "__main__":
    main()
