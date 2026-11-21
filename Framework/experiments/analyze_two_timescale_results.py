"""Paired statistical analysis for the targeted two-timescale SimPy evaluation.

This script does not run a simulation. It analyses the 30-seed paired output
CSV in results/supplementary/two_timescale/30_seed_evaluation/ and writes
seed-level statistics, a concise report, and figures beside the source data.
"""
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
DEFAULT_INPUT = ROOT / "results" / "supplementary" / "two_timescale" / "30_seed_evaluation"

METRICS = {
    "PDR": ("higher", "Packet delivery ratio", "fraction"),
    "Mean_Latency_s": ("lower", "Mean end-to-end latency", "seconds"),
    "P95_Latency_s": ("lower", "P95 end-to-end latency", "seconds"),
    "Emergency_PDR": ("higher", "Emergency packet delivery ratio", "fraction"),
    "Total_Modelled_Energy_J": ("lower", "Total modelled energy", "joules"),
    "Mean_Decision_Time_us": ("lower", "Mean decision computation time", "microseconds"),
}
BASELINE = "ADAPTIVE_AHP_TOPSIS"
PROPOSED = "TWO_TIMESCALE"


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, returned in original order."""
    n = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(n, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        value = min(1.0, (n - rank) * float(p_values[idx]))
        running = max(running, value)
        adjusted[idx] = running
    return adjusted.tolist()


def paired_stats(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seed_rows = []
    rows = []
    pvals = []
    for metric, (direction, label, unit) in METRICS.items():
        pivot = frame.pivot(index="Seed", columns="Algorithm", values=metric).sort_index()
        if BASELINE not in pivot or PROPOSED not in pivot:
            raise ValueError(f"Missing algorithm rows for {metric}: expected {BASELINE} and {PROPOSED}")
        base = pivot[BASELINE].astype(float)
        prop = pivot[PROPOSED].astype(float)
        diff = prop - base
        valid = diff.dropna()
        if valid.empty:
            raise ValueError(f"No paired observations for {metric}")
        if np.allclose(valid.to_numpy(), 0.0):
            wilcoxon_stat, p_value = 0.0, 1.0
        else:
            result = stats.wilcoxon(valid.to_numpy(), zero_method="wilcox", alternative="two-sided", method="auto")
            wilcoxon_stat, p_value = float(result.statistic), float(result.pvalue)
        if len(valid) > 1 and valid.std(ddof=1) > 0:
            ci_low, ci_high = stats.t.interval(
                0.95, len(valid) - 1, loc=valid.mean(), scale=stats.sem(valid)
            )
        else:
            ci_low = ci_high = float(valid.mean())
        better = (diff > 0) if direction == "higher" else (diff < 0)
        worse = (diff < 0) if direction == "higher" else (diff > 0)
        rows.append({
            "metric": metric,
            "label": label,
            "unit": unit,
            "baseline_mean": float(base.mean()),
            "proposed_mean": float(prop.mean()),
            "paired_mean_difference_proposed_minus_baseline": float(valid.mean()),
            "relative_difference_percent": float(valid.mean() / base.mean() * 100) if abs(base.mean()) > 1e-15 else None,
            "paired_difference_95pct_t_ci_low": float(ci_low),
            "paired_difference_95pct_t_ci_high": float(ci_high),
            "wilcoxon_statistic": wilcoxon_stat,
            "wilcoxon_p_raw": p_value,
            "better_seeds": int(better.sum()),
            "tied_seeds": int((diff == 0).sum()),
            "worse_seeds": int(worse.sum()),
            "n_paired_seeds": int(valid.size),
        })
        pvals.append(p_value)
        for seed, bval, pval, dval in zip(pivot.index, base, prop, diff):
            seed_rows.append({
                "Seed": int(seed), "Metric": metric,
                "Baseline": float(bval), "Two_Timescale": float(pval),
                "Difference_Proposed_Minus_Baseline": float(dval),
            })
    adjusted = holm_adjust(pvals)
    for row, p_adj in zip(rows, adjusted):
        row["wilcoxon_p_holm_adjusted_6_metrics"] = p_adj
        row["significant_after_holm_0_05"] = bool(p_adj < 0.05)
    return pd.DataFrame(rows), pd.DataFrame(seed_rows)


def aggregate_summary(frame: pd.DataFrame) -> dict:
    output = {}
    for algorithm, g in frame.groupby("Algorithm"):
        generated = int(g["Generated"].sum())
        delivered = int(g["Delivered"].sum())
        emergency_generated = int(g["Emergency_Generated"].sum())
        emergency_delivered = int(g["Emergency_Delivered"].sum())
        energy = float(g["Total_Modelled_Energy_J"].sum())
        output[algorithm] = {
            "seeds": int(g["Seed"].nunique()),
            "generated_packets": generated,
            "delivered_packets": delivered,
            "pooled_pdr": delivered / generated if generated else None,
            "emergency_generated": emergency_generated,
            "emergency_delivered": emergency_delivered,
            "pooled_emergency_pdr": emergency_delivered / emergency_generated if emergency_generated else None,
            "total_modelled_energy_j": energy,
            "energy_per_delivered_packet_j": energy / delivered if delivered else None,
            "qos_drops": int(g["QoS_Drops"].sum()),
            "outage_drops": int(g["Outage_Drops"].sum()),
            "reliability_drops": int(g["Reliability_Drops"].sum()),
            "nb_selections": int(g["NB_Selections"].sum()),
            "5g_selections": int(g["5G_Selections"].sum()),
            "packet_selection_changes": int(g["Packet_Selection_Changes"].sum()),
            "mean_decision_time_us_across_seeds": float(g["Mean_Decision_Time_us"].mean()),
        }
    return output


def make_scatter(frame: pd.DataFrame, metric: str, title: str, filename: Path, unit: str, percent: bool = False):
    pivot = frame.pivot(index="Seed", columns="Algorithm", values=metric).sort_index()
    x = pivot[BASELINE].astype(float).to_numpy()
    y = pivot[PROPOSED].astype(float).to_numpy()
    if percent:
        x, y = x * 100, y * 100
        unit = "%"
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    ax.scatter(x, y, alpha=0.78)
    lo = float(min(x.min(), y.min()))
    hi = float(max(x.max(), y.max()))
    span = hi - lo
    pad = span * 0.08 if span > 0 else max(abs(hi) * 0.08, 0.01)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], linestyle="--", linewidth=1)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel(f"Existing AHP-TOPSIS ({unit})")
    ax.set_ylabel(f"Two-timescale controller ({unit})")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(filename, dpi=180)
    plt.close(fig)


def make_decision_timeline(decisions: pd.DataFrame, metadata: dict, filename: Path) -> dict:
    outage = metadata.get("event", {})
    start = float(outage.get("start_s", 40.0))
    end = start + float(outage.get("duration_s", 20.0))
    bins = np.arange(0, float(metadata.get("duration_s", 120.0)) + 5, 5)
    d = decisions.copy()
    d["bin"] = pd.cut(d["arrival_time_s"], bins=bins, right=False, include_lowest=True)
    grouped = d.groupby("bin", observed=False).agg(
        decisions=("pid", "count"), five_g=("selected_network", lambda s: int((s == 1).sum()))
    )
    grouped["five_g_share"] = grouped.apply(lambda r: r.five_g / r.decisions if r.decisions else np.nan, axis=1)
    x = [(b.left + b.right) / 2 for b in grouped.index]
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    ax.plot(x, grouped["five_g_share"].to_numpy(), marker="o", linewidth=1.4)
    ax.axvspan(start, end, alpha=0.18, label="5G outage")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Simulation time (s)")
    ax.set_ylabel("Share of TSC decisions selecting 5G")
    ax.set_title("Two-timescale controller: selected backhaul over time")
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(filename, dpi=180)
    plt.close(fig)
    in_outage = d[(d.arrival_time_s >= start) & (d.arrival_time_s < end)]
    after = d[d.arrival_time_s >= end]
    return {
        "outage_start_s": start,
        "outage_end_s": end,
        "outage_decisions": int(len(in_outage)),
        "outage_all_selected_nb_iot": bool(len(in_outage) and (in_outage.selected_network == 0).all()),
        "post_outage_decisions": int(len(after)),
        "post_outage_5g_selections": int((after.selected_network == 1).sum()),
        "post_outage_nb_selections": int((after.selected_network == 0).sum()),
        "post_outage_5g_share": float((after.selected_network == 1).mean()) if len(after) else None,
    }


def make_selection_share(frame: pd.DataFrame, filename: Path) -> pd.DataFrame:
    rows = []
    for alg, group in frame.groupby("Algorithm"):
        nb = int(group.NB_Selections.sum())
        g5 = int(group["5G_Selections"].sum())
        n = nb + g5
        rows.extend([
            {"Algorithm": alg, "Backhaul": "NB-IoT", "Selections": nb, "Share": nb / n if n else 0},
            {"Algorithm": alg, "Backhaul": "5G NR", "Selections": g5, "Share": g5 / n if n else 0},
        ])
    out = pd.DataFrame(rows)
    pivot = out.pivot(index="Algorithm", columns="Backhaul", values="Share")
    ax = pivot.plot(kind="bar", figsize=(7.0, 4.4))
    ax.set_ylabel("Share of packet selections")
    ax.set_xlabel("")
    ax.set_title("Backhaul selection share across the 30 paired runs")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(filename, dpi=180)
    plt.close()
    return out


def write_report(out_dir: Path, metadata: dict, aggregate: dict, paired: pd.DataFrame, event_summary: dict, shares: pd.DataFrame) -> None:
    b = aggregate[BASELINE]
    p = aggregate[PROPOSED]
    pdr_row = paired.loc[paired.metric == "PDR"].iloc[0]
    lat_row = paired.loc[paired.metric == "Mean_Latency_s"].iloc[0]
    p95_row = paired.loc[paired.metric == "P95_Latency_s"].iloc[0]
    energy_row = paired.loc[paired.metric == "Total_Modelled_Energy_J"].iloc[0]
    overhead_row = paired.loc[paired.metric == "Mean_Decision_Time_us"].iloc[0]
    mode_counts = pd.read_csv(out_dir / "targeted_smoke_decisions.csv")["decision_mode"].value_counts().to_dict()
    pdr_pp = (p["pooled_pdr"] - b["pooled_pdr"]) * 100
    energy_delta_pct = (p["total_modelled_energy_j"] / b["total_modelled_energy_j"] - 1) * 100
    latency_reduction = (1 - p["mean_decision_time_us_across_seeds"] / b["mean_decision_time_us_across_seeds"]) * 100
    lines = [
        "# 30-Seed Paired Evaluation — Two-Timescale Backhaul Controller",
        "",
        f"**Simulation horizon:** {metadata['duration_s']} s per seed  ",
        f"**Offered load:** {metadata['offered_load_pps']} packets/s  ",
        f"**Emergency traffic:** {metadata['emergency_ratio']:.0%}  ",
        f"**Seeds:** {len(metadata['seeds'])} ({metadata['seeds'][0]}–{metadata['seeds'][-1]})  ",
        f"**Outage:** {event_summary['outage_start_s']:.0f}–{event_summary['outage_end_s']:.0f} s  ",
        f"**Wall runtime recorded by runner:** {metadata['wall_runtime_s']:.3f} s",
        "",
        "> **Evidence classification:** targeted paired simulation evaluation (exploratory). It is not the original 3,600-second baseline experiment and does not establish performance across all traffic loads or outage patterns.",
        "",
        "## 1. Aggregate outcome",
        "",
        "| Metric | Existing AHP-TOPSIS | Two-timescale |",
        "|---|---:|---:|",
        f"| Generated packets | {b['generated_packets']:,} | {p['generated_packets']:,} |",
        f"| Delivered packets | {b['delivered_packets']:,} | {p['delivered_packets']:,} |",
        f"| Pooled PDR | {b['pooled_pdr']*100:.4f}% | {p['pooled_pdr']*100:.4f}% |",
        f"| Emergency PDR | {b['pooled_emergency_pdr']*100:.4f}% | {p['pooled_emergency_pdr']*100:.4f}% |",
        f"| Total modelled energy | {b['total_modelled_energy_j']:.4f} J | {p['total_modelled_energy_j']:.4f} J |",
        f"| Energy / delivered packet | {b['energy_per_delivered_packet_j']:.8f} J | {p['energy_per_delivered_packet_j']:.8f} J |",
        f"| QoS drops | {b['qos_drops']} | {p['qos_drops']} |",
        f"| Outage drops | {b['outage_drops']} | {p['outage_drops']} |",
        f"| Reliability drops | {b['reliability_drops']} | {p['reliability_drops']} |",
        f"| Mean decision time (mean across seeds) | {b['mean_decision_time_us_across_seeds']:.2f} µs | {p['mean_decision_time_us_across_seeds']:.2f} µs |",
        "",
        f"The pooled PDR difference is **{pdr_pp:+.4f} percentage points**. Mean latency decreases by **{-lat_row.paired_mean_difference_proposed_minus_baseline:.4f} s** when comparing per-seed means; mean P95 decreases by **{-p95_row.paired_mean_difference_proposed_minus_baseline:.4f} s**. Total modelled energy changes by **{energy_delta_pct:+.3f}%**. Mean measured selector time decreases by **{latency_reduction:.2f}%** in this runtime environment.",
        "",
        "## 2. Paired statistical analysis",
        "",
        "The unit of analysis is the paired seed (n=30). Two-sided Wilcoxon signed-rank tests compare per-seed metrics. Holm-Bonferroni correction is applied across the six reported endpoints. The 95% confidence interval is a paired t-interval for the mean within-seed difference (proposed minus baseline). These are exploratory tests because the run is one traffic load, one horizon and one outage schedule.",
        "",
        "| Endpoint | Mean paired difference (TSC − AHP) | 95% paired t CI | Raw Wilcoxon p | Holm-adjusted p | Seeds better / tied / worse |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in paired.iterrows():
        unit = r.unit
        diff = r.paired_mean_difference_proposed_minus_baseline
        ci = f"[{r.paired_difference_95pct_t_ci_low:.6g}, {r.paired_difference_95pct_t_ci_high:.6g}]"
        counts = f"{int(r.better_seeds)} / {int(r.tied_seeds)} / {int(r.worse_seeds)}"
        lines.append(f"| {r.label} | {diff:+.6g} {unit} | {ci} | {r.wilcoxon_p_raw:.4g} | {r.wilcoxon_p_holm_adjusted_6_metrics:.4g} | {counts} |")
    lines += [
        "",
        "**Interpretation:** mean latency, P95 latency and decision computation time remain statistically different after the six-endpoint Holm correction in this targeted experiment. PDR has a small positive raw paired difference, but it does **not** survive Holm correction. Emergency PDR is identical. Total modelled energy has no statistically supported difference. Statistical significance for selector computation time does not imply end-to-end network performance superiority.",
        "",
        "## 3. Controller decision evidence",
        "",
        f"- Recorded TSC decisions: {sum(mode_counts.values()):,}.",
        f"- Decision modes: `{json.dumps(mode_counts, sort_keys=True)}`.",
        f"- Persistent controller switch events: {int(pd.read_csv(out_dir / 'targeted_smoke_metrics.csv').loc[lambda x: x.Algorithm == PROPOSED, 'Persistent_Controller_Switches'].sum())}.",
        f"- Packet-level QoS overrides: {int(pd.read_csv(out_dir / 'targeted_smoke_metrics.csv').loc[lambda x: x.Algorithm == PROPOSED, 'Packet_QoS_Overrides'].sum())}.",
        f"- Forced fallbacks: {int(pd.read_csv(out_dir / 'targeted_smoke_metrics.csv').loc[lambda x: x.Algorithm == PROPOSED, 'Forced_Fallbacks'].sum())}.",
        f"- During the configured outage, {event_summary['outage_decisions']:,} recorded decisions selected NB-IoT only: {event_summary['outage_all_selected_nb_iot']}.",
        f"- After outage recovery, the controller selected 5G in {event_summary['post_outage_5g_share']*100:.2f}% of recorded packet decisions.",
        "",
        "The outage scenario demonstrates functional fallback and recovery. It does not prove better outage performance than AHP-TOPSIS: both methods had two packet-level network changes per seed on average, and the two-timescale method had 62 persistent switch events compared with 60 baseline packet-selection changes. The experiment therefore does not demonstrate reduced switching in this particular outage trace.",
        "",
        "## 4. What the results support",
        "",
        "**Supported for this targeted configuration**",
        "- The two-timescale controller executed in SimPy over 30 paired input traces.",
        "- It produced a slightly higher pooled PDR (+9 delivered packets across 7,051 generated), driven by nine fewer reliability drops; the emergency PDR did not change.",
        "- It produced lower per-seed mean and P95 latency in a subset of runs and was never worse on these two latency averages in this dataset (ties are common).",
        "- It used less selector computation time in all 30 paired runs.",
        "- It performed fallback to NB-IoT for all decisions recorded during the 5G outage window and reselected 5G after recovery in most post-outage decisions.",
        "",
        "**Not established**",
        "- Lower total energy: total modelled energy was slightly higher (+0.098%) and the difference is not statistically significant.",
        "- Better emergency PDR: identical between methods (599/699 delivered).",
        "- Reduced handover/switching: not demonstrated in this experiment.",
        "- General superiority across loads, session patterns, longer horizons or multiple outage patterns.",
        "- Real modem energy efficiency or hardware battery lifetime.",
        "",
        "## 5. Model and experiment limitations",
        "",
        "1. The evaluation uses one offered load (2 packets/s), a 120-second horizon, 10% emergency traffic and one 20-second 5G outage.",
        "2. Idle-tail power and switching energy are configured as zero because the source simulator does not provide calibrated values; modelled energy includes CPU, setup and transmission components.",
        "3. The expected burst size uses a Poisson gap-cluster approximation and an EWMA arrival-rate estimate; it is not a learned or measured traffic forecast.",
        "4. Latency feasibility uses deterministic predicted delay; no probabilistic deadline guarantee is modelled.",
        "5. AHP-TOPSIS and the new controller share the same underlying simplified modem and network abstractions. This is not a physical NB-IoT/5G deployment.",
        "6. The decision-time comparison is software timing in one execution environment, not a hardware-independent complexity proof.",
        "7. P-values are exploratory. The small PDR effect is not significant after multiple-endpoint correction.",
        "",
        "## 6. Reproduction",
        "",
        "From `Framework/`:",
        "```powershell",
        "py -3.13 -m pip install -r requirements.txt",
        "py -3.13 experiments/run_two_timescale_smoke.py --duration-s 120 --rate-pps 2 --emergency-ratio 0.10 --seeds 1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029 --outage-start-s 40 --outage-duration-s 20",
        "py -3.13 experiments/analyze_two_timescale_results.py",
        "```",
        "",
        "The first command reproduces the dependency setup; the second reruns the targeted 30-seed evaluation and overwrites only the targeted output CSVs in this supplementary folder; the third generates statistical summaries and figures. Historical primary results are not touched.",
        "",
        "## 7. Generated figures",
        "",
        "- `pdr_paired_scatter.png`",
        "- `mean_latency_paired_scatter.png`",
        "- `p95_latency_paired_scatter.png`",
        "- `energy_paired_scatter.png`",
        "- `decision_time_paired_scatter.png`",
        "- `backhaul_selection_share.png`",
        "- `outage_selection_timeline.png`",
        "",
    ]
    (out_dir / "30_SEED_EVALUATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = input_dir / "targeted_smoke_metrics.csv"
    decisions_path = input_dir / "targeted_smoke_decisions.csv"
    metadata_path = input_dir / "targeted_smoke_metadata.json"
    frame = pd.read_csv(metrics_path)
    decisions = pd.read_csv(decisions_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if len(metadata.get("seeds", [])) != frame.Seed.nunique():
        raise ValueError("Metadata seed list does not match metric rows")
    counts = frame.groupby("Algorithm")["Seed"].nunique().to_dict()
    if counts.get(BASELINE) != counts.get(PROPOSED):
        raise ValueError(f"Paired seed count mismatch: {counts}")
    paired, seed_diffs = paired_stats(frame)
    paired.to_csv(output_dir / "paired_statistics.csv", index=False)
    seed_diffs.to_csv(output_dir / "seed_level_differences.csv", index=False)
    aggregate = aggregate_summary(frame)
    (output_dir / "aggregate_summary.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    shares = make_selection_share(frame, output_dir / "backhaul_selection_share.png")
    shares.to_csv(output_dir / "backhaul_selection_share.csv", index=False)
    make_scatter(frame, "PDR", "Paired PDR by random seed", output_dir / "pdr_paired_scatter.png", "fraction", percent=True)
    make_scatter(frame, "Mean_Latency_s", "Paired mean latency by random seed", output_dir / "mean_latency_paired_scatter.png", "s")
    make_scatter(frame, "P95_Latency_s", "Paired P95 latency by random seed", output_dir / "p95_latency_paired_scatter.png", "s")
    make_scatter(frame, "Total_Modelled_Energy_J", "Paired total modelled energy by random seed", output_dir / "energy_paired_scatter.png", "J")
    make_scatter(frame, "Mean_Decision_Time_us", "Paired selector computation time by random seed", output_dir / "decision_time_paired_scatter.png", "µs")
    event_summary = make_decision_timeline(decisions, metadata, output_dir / "outage_selection_timeline.png")
    (output_dir / "event_summary.json").write_text(json.dumps(event_summary, indent=2), encoding="utf-8")
    write_report(output_dir, metadata, aggregate, paired, event_summary, shares)
    print(f"Analysed {frame.Seed.nunique()} paired seeds and {len(decisions)} TSC decisions.")
    print(f"Wrote report, statistical CSVs and figures to: {output_dir}")


if __name__ == "__main__":
    main()
