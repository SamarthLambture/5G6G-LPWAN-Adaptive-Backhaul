from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = ROOT / "results" / "raw" / "raw_paired_metrics.csv"
PAIRED_FILE = ROOT / "results" / "processed" / "paired_stats.csv"
SELECTION_FILE = ROOT / "results" / "processed" / "selection_analysis.csv"

FIG_DIR = ROOT / "results" / "figures"
TABLE_DIR = ROOT / "results" / "tables"

FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(RAW_FILE)
paired = pd.read_csv(PAIRED_FILE)
selection = pd.read_csv(SELECTION_FILE)

ALGORITHMS = ["NB", "5G", "LAT", "ENG", "TOP", "AHP"]

def save_plot(filename):
    plt.tight_layout()
    plt.savefig(FIG_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure: {filename}")

def scenario_means(scenarios, algorithms=None):
    data = raw[raw["Scenario"].isin(scenarios)].copy()
    if algorithms is not None:
        data = data[data["Algorithm"].isin(algorithms)]
    return data.groupby(["Scenario", "Algorithm"], as_index=False).mean(
        numeric_only=True
    )

# ---------------------------------------------------------
# 1. BASELINE SUMMARY TABLE
# ---------------------------------------------------------

baseline = raw[raw["Scenario"] == "A_NORMAL"].copy()

metrics = [
    "PDR",
    "Avg_Lat_s",
    "95th_Lat_s",
    "Total_Eng_J",
    "Throughput_bps",
    "Emerg_PDR",
    "Emerg_Lat_s",
    "QoS_Violations_Deliv",
    "QoS_Drop",
    "Switches",
    "Algo_Time_Mean_us",
    "Algo_Time_Max_us",
]

summary_rows = []

for algorithm in ALGORITHMS:
    subset = baseline[baseline["Algorithm"] == algorithm]
    row = {"Algorithm": algorithm, "Seeds": len(subset)}

    for metric in metrics:
        values = subset[metric].dropna()
        row[f"{metric}_Mean"] = values.mean()
        row[f"{metric}_Std"] = values.std()
        sample_sd = values.std(ddof=1) if len(values) > 1 else np.nan
        row[f"{metric}_CI95"] = (
            2.045 * sample_sd / np.sqrt(len(values))
            if len(values) > 1 and np.isfinite(sample_sd) and sample_sd > 0
            else np.nan
        )

    summary_rows.append(row)

baseline_summary = pd.DataFrame(summary_rows)
baseline_summary.to_csv(
    TABLE_DIR / "baseline_algorithm_summary.csv", index=False
)

print("Saved table: baseline_algorithm_summary.csv")

# ---------------------------------------------------------
# 2. BASELINE ALGORITHM COMPARISON FIGURE
# ---------------------------------------------------------

fig, axes = plt.subplots(1, 3, figsize=(17, 5))

baseline_plot = baseline_summary.set_index("Algorithm").loc[ALGORITHMS]

plots = [
    ("PDR_Mean", "PDR_CI95", "Packet Delivery Ratio", "PDR"),
    ("Avg_Lat_s_Mean", "Avg_Lat_s_CI95", "Average Latency", "Seconds"),
    ("Total_Eng_J_Mean", "Total_Eng_J_CI95", "Total Energy", "Joules"),
]

for ax, (mean_col, ci_col, title, ylabel) in zip(axes, plots):
    values = baseline_plot[mean_col].values
    errors = baseline_plot[ci_col].values

    ax.bar(ALGORITHMS, values, yerr=errors, capsize=4)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)

fig.suptitle("Baseline Performance Comparison — A_NORMAL")
save_plot("01_baseline_algorithm_comparison.png")

# ---------------------------------------------------------
# 3. LOAD SWEEP
# ---------------------------------------------------------

load_rows = []

for scenario in raw["Scenario"].unique():
    match = re.fullmatch(r"G_LOAD_(\d+(?:\.\d+)?)", scenario)
    if match:
        load_rows.append((float(match.group(1)), scenario))

load_rows.sort()

load_data = raw[
    raw["Scenario"].isin([scenario for _, scenario in load_rows])
]

load_summary = load_data.groupby(
    ["Scenario", "Algorithm"], as_index=False
).mean(numeric_only=True)

load_summary.to_csv(TABLE_DIR / "load_sweep_summary.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for algorithm in ["NB", "AHP"]:
    subset = load_summary[load_summary["Algorithm"] == algorithm].copy()
    subset["Load"] = subset["Scenario"].map(
        {scenario: load for load, scenario in load_rows}
    )
    subset = subset.sort_values("Load")

    axes[0].plot(
        subset["Load"], subset["PDR"] * 100,
        marker="o", label=algorithm
    )
    axes[1].plot(
        subset["Load"], subset["Avg_Lat_s"],
        marker="o", label=algorithm
    )

axes[0].set_title("Packet Delivery vs Offered Load")
axes[0].set_xlabel("Offered Load (packets/second)")
axes[0].set_ylabel("PDR (%)")

axes[1].set_title("Average Latency vs Offered Load")
axes[1].set_xlabel("Offered Load (packets/second)")
axes[1].set_ylabel("Average Latency (seconds)")

for ax in axes:
    ax.legend()
    ax.grid(alpha=0.25)

save_plot("02_load_sweep.png")

# ---------------------------------------------------------
# 4. ENERGY SENSITIVITY
# ---------------------------------------------------------

energy_scenarios = [
    "H_ENG_NB_NEG50",
    "H_ENG_NB_POS50",
    "H_ENG_BASE",
    "H_ENG_5G_NEG50",
    "H_ENG_5G_POS50",
]

energy_summary = scenario_means(energy_scenarios, ["NB", "AHP"])
energy_summary.to_csv(
    TABLE_DIR / "energy_sensitivity_summary.csv", index=False
)

energy_order = [
    "H_ENG_NB_NEG50",
    "H_ENG_NB_POS50",
    "H_ENG_BASE",
    "H_ENG_5G_NEG50",
    "H_ENG_5G_POS50",
]

energy_labels = [
    "NB energy\n-50%",
    "NB energy\n+50%",
    "Baseline",
    "5G energy\n-50%",
    "5G energy\n+50%",
]

fig, ax = plt.subplots(figsize=(11, 5))
x = np.arange(len(energy_order))
width = 0.36

for offset, algorithm in [(-width / 2, "NB"), (width / 2, "AHP")]:
    subset = energy_summary[
        energy_summary["Algorithm"] == algorithm
    ].set_index("Scenario").reindex(energy_order)

    ax.bar(
        x + offset,
        subset["Total_Eng_J"],
        width,
        label=algorithm
    )

ax.set_xticks(x)
ax.set_xticklabels(energy_labels)
ax.set_ylabel("Total Energy (J)")
ax.set_title("Energy Sensitivity Analysis")
ax.legend()
ax.grid(axis="y", alpha=0.25)

save_plot("03_energy_sensitivity.png")

# ---------------------------------------------------------
# 5. RELIABILITY SENSITIVITY
# ---------------------------------------------------------

nb_reliability = {
    "I_REL_NB_1": 1,
    "I_REL_NB_5": 5,
    "I_REL_NB_10": 10,
}

g5_reliability = {
    "I_REL_5G_1": 1,
    "I_REL_5G_5": 5,
    "I_REL_5G_10": 10,
}

reliability_rows = []

for scenario, loss in nb_reliability.items():
    subset = raw[
        (raw["Scenario"] == scenario) &
        (raw["Algorithm"] == "NB")
    ]
    reliability_rows.append({
        "Backhaul": "NB-IoT",
        "Configured_Loss_Pct": loss,
        "PDR_Mean": subset["PDR"].mean(),
        "Latency_Mean_s": subset["Avg_Lat_s"].mean(),
    })

for scenario, loss in g5_reliability.items():
    subset = raw[
        (raw["Scenario"] == scenario) &
        (raw["Algorithm"] == "5G")
    ]
    reliability_rows.append({
        "Backhaul": "5G",
        "Configured_Loss_Pct": loss,
        "PDR_Mean": subset["PDR"].mean(),
        "Latency_Mean_s": subset["Avg_Lat_s"].mean(),
    })

reliability_summary = pd.DataFrame(reliability_rows)
reliability_summary.to_csv(
    TABLE_DIR / "reliability_sensitivity_summary.csv", index=False
)

fig, ax = plt.subplots(figsize=(8, 5))

for backhaul in ["NB-IoT", "5G"]:
    subset = reliability_summary[
        reliability_summary["Backhaul"] == backhaul
    ].sort_values("Configured_Loss_Pct")

    ax.plot(
        subset["Configured_Loss_Pct"],
        subset["PDR_Mean"] * 100,
        marker="o",
        label=backhaul
    )

ax.set_title("Packet Delivery under Reliability Sensitivity")
ax.set_xlabel("Configured Link Loss (%)")
ax.set_ylabel("Measured PDR (%)")
ax.legend()
ax.grid(alpha=0.25)

save_plot("04_reliability_sensitivity.png")

# ---------------------------------------------------------
# 6. ADAPTIVE AHP SELECTION DISTRIBUTION
# ---------------------------------------------------------

selection_scenario = selection.groupby(
    "Scenario", as_index=False
)[["NB_Sel", "5G_Sel", "Total_Decisions"]].sum()

selection_scenario["NB_Sel_Pct"] = np.where(
    selection_scenario["Total_Decisions"] > 0,
    selection_scenario["NB_Sel"] /
    selection_scenario["Total_Decisions"] * 100,
    np.nan
)

selection_scenario["5G_Sel_Pct"] = np.where(
    selection_scenario["Total_Decisions"] > 0,
    selection_scenario["5G_Sel"] /
    selection_scenario["Total_Decisions"] * 100,
    np.nan
)

selection_scenario.to_csv(
    TABLE_DIR / "ahp_selection_by_scenario.csv", index=False
)

selection_state = selection.groupby(
    "AHP_State", as_index=False
)[["NB_Sel", "5G_Sel", "Total_Decisions"]].sum()

selection_state["NB_Sel_Pct"] = np.where(
    selection_state["Total_Decisions"] > 0,
    selection_state["NB_Sel"] /
    selection_state["Total_Decisions"] * 100,
    np.nan
)

selection_state["5G_Sel_Pct"] = np.where(
    selection_state["Total_Decisions"] > 0,
    selection_state["5G_Sel"] /
    selection_state["Total_Decisions"] * 100,
    np.nan
)

selection_state.to_csv(
    TABLE_DIR / "ahp_selection_by_state.csv", index=False
)

fig, ax = plt.subplots(figsize=(15, 6))

plot_selection = selection_scenario.sort_values("Scenario")
x = np.arange(len(plot_selection))

ax.bar(
    x,
    plot_selection["NB_Sel_Pct"],
    label="NB-IoT"
)

ax.bar(
    x,
    plot_selection["5G_Sel_Pct"],
    bottom=plot_selection["NB_Sel_Pct"],
    label="5G"
)

ax.set_xticks(x)
ax.set_xticklabels(
    plot_selection["Scenario"],
    rotation=65,
    ha="right"
)
ax.set_ylabel("Share of AHP Decisions (%)")
ax.set_ylim(0, 105)
ax.set_title("Adaptive AHP-TOPSIS Backhaul Selection by Scenario")
ax.legend()
ax.grid(axis="y", alpha=0.25)

save_plot("05_ahp_selection_by_scenario.png")

# State-level selection figure
fig, ax = plt.subplots(figsize=(8, 5))

state_order = ["NORMAL", "EMERGENCY", "LOW_BATTERY", "CONFLICT"]
state_plot = selection_state.set_index("AHP_State").reindex(state_order)

ax.bar(state_order, state_plot["NB_Sel_Pct"], label="NB-IoT")
ax.bar(
    state_order,
    state_plot["5G_Sel_Pct"],
    bottom=state_plot["NB_Sel_Pct"],
    label="5G"
)

ax.set_ylabel("Share of AHP Decisions (%)")
ax.set_ylim(0, 105)
ax.set_title("Backhaul Selection by AHP Operating State")
ax.legend()
ax.grid(axis="y", alpha=0.25)

save_plot("06_ahp_selection_by_state.png")

# ---------------------------------------------------------
# 7. ALGORITHM EXECUTION OVERHEAD
# ---------------------------------------------------------

overhead = raw[raw["Scenario"] == "J_OVERHEAD"].groupby(
    "Algorithm", as_index=False
).agg(
    Mean_Overhead_us=("Algo_Time_Mean_us", "mean"),
    Max_Overhead_us=("Algo_Time_Max_us", "mean"),
)

overhead.to_csv(
    TABLE_DIR / "algorithm_overhead_summary.csv", index=False
)

overhead = overhead.set_index("Algorithm").reindex(ALGORITHMS).reset_index()

fig, ax = plt.subplots(figsize=(9, 5))

ax.bar(
    overhead["Algorithm"],
    overhead["Mean_Overhead_us"]
)

ax.set_title("Mean Algorithm Execution Time — J_OVERHEAD")
ax.set_ylabel("Mean Execution Time (microseconds)")
ax.set_xlabel("Algorithm")
ax.grid(axis="y", alpha=0.25)

save_plot("07_algorithm_overhead.png")

# ---------------------------------------------------------
# 8. SUPPLEMENTARY FIVE-SEED 5G-OUTAGE / RECOVERY PILOT
# ---------------------------------------------------------

OUTAGE_FILE = ROOT / "results" / "supplementary" / "5g_outage" / "raw_metrics.csv"
if OUTAGE_FILE.exists():
    outage_raw = pd.read_csv(OUTAGE_FILE)
    outage_summary = outage_raw.groupby("Algorithm", as_index=False).agg(
        PDR_Mean=("PDR", "mean"),
        Emergency_PDR_Mean=("Emergency_PDR", "mean"),
        Mean_Latency_s=("Mean_Latency_s", "mean"),
        Total_Energy_J=("Total_Energy_J", "mean"),
        NB_Selections_During_Outage=("NB_Selections_During_5G_Outage", "mean"),
        FiveG_Selections_During_Outage=("5G_Selections_During_5G_Outage", "mean"),
        FiveG_Selections_After_Recovery=("5G_Selections_After_Recovery", "mean"),
        Selection_Changes=("Switches", "mean"),
        QoS_Drops=("QoS_Drops", "mean"),
        Outage_Drops=("Outage_Drops", "mean"),
    )
    outage_summary.to_csv(TABLE_DIR / "5g_outage_summary.csv", index=False)
    outage_summary = outage_summary.set_index("Algorithm").reindex(ALGORITHMS).reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].bar(outage_summary["Algorithm"], outage_summary["PDR_Mean"] * 100)
    axes[0].set_title("Packet delivery ratio")
    axes[0].set_ylabel("PDR (%)")
    axes[1].bar(outage_summary["Algorithm"], outage_summary["NB_Selections_During_Outage"])
    axes[1].set_title("NB-IoT selections during 5G outage")
    axes[1].set_ylabel("Mean selections per seed")
    axes[2].bar(outage_summary["Algorithm"], outage_summary["Selection_Changes"])
    axes[2].set_title("Selected-backhaul label changes")
    axes[2].set_ylabel("Mean changes per seed")
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Supplementary 5G-Outage / Recovery Pilot (5 seeds; separate from primary matrix)")
    save_plot("08_5g_outage_failover.png")
else:
    print("Supplementary 5G-outage pilot data not found; keeping the primary figures separate.")

# ---------------------------------------------------------
# 9. EXPORT PAIRED STATISTICS FOR REPORT
# ---------------------------------------------------------

paired.to_csv(
    TABLE_DIR / "paired_statistics_for_report.csv",
    index=False
)

print("\n======================================")
print("FIGURE GENERATION COMPLETED")
print("======================================")
print("Figures directory:", FIG_DIR)
print("Tables directory:", TABLE_DIR)
print(f"Figures generated: {8 if OUTAGE_FILE.exists() else 7}")
print("Summary tables exported.")
