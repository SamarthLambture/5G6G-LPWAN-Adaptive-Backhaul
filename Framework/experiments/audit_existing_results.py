"""Generate reproducible mathematical/statistical diagnostics from archived results.

This script does not need SimPy and does not rerun or modify the simulation.
It reads the primary CSV outputs and writes transparent audit tables.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.math_engine import DynamicAHP  # noqa: E402
from src.core.paired_statistics import paired_t_summary  # noqa: E402

RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

METRICS = {
    "PDR": "PDR",
    "Avg_Lat_s": "Average latency (s)",
    "Total_Eng_J": "Total energy (J)",
}


def markdown_table(frame: pd.DataFrame) -> str:
    """Small dependency-free Markdown table renderer for audit reports."""
    columns = [str(column) for column in frame.columns]

    def cell(value):
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.6f}"
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines)


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Return Benjamini-Hochberg FDR-adjusted q-values in original order."""
    p_values = np.asarray(p_values, dtype=float)
    if p_values.ndim != 1:
        raise ValueError("p-values must be one-dimensional")
    if np.any(~np.isfinite(p_values)) or np.any((p_values < 0) | (p_values > 1)):
        raise ValueError("p-values must be finite and within [0, 1]")
    m = len(p_values)
    if m == 0:
        return np.array([], dtype=float)

    order = np.argsort(p_values)
    ranked = p_values[order]
    adjusted = ranked * m / np.arange(1, m + 1, dtype=float)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    output = np.empty_like(adjusted)
    output[order] = adjusted
    return output


def build_ahp_validation() -> pd.DataFrame:
    ahp = DynamicAHP()
    rows = []
    for state, matrix in ahp.matrices.items():
        weights, cr = ahp.calculate_weights(matrix)
        rows.append(
            {
                "AHP_State": state,
                "Matrix_Size": matrix.shape[0],
                "Weights_Latency": weights[0],
                "Weights_Energy": weights[1],
                "Weights_Reliability": weights[2],
                "Weights_Bandwidth": weights[3],
                "Lambda_Max": float(np.max(np.linalg.eigvals(matrix).real)),
                "Consistency_Index": 0.0,
                "Random_Index_n4": ahp.RANDOM_INDEX[matrix.shape[0]],
                "Consistency_Ratio": cr,
                "Reciprocal": bool(np.allclose(matrix * matrix.T, 1.0)),
                "Diagonal_One": bool(np.allclose(np.diag(matrix), 1.0)),
                "Interpretation": "Design-specified ratio matrix; perfect consistency is by construction.",
            }
        )
    return pd.DataFrame(rows)


def build_selection_diagnostics() -> tuple[pd.DataFrame, pd.DataFrame]:
    source = RESULTS / "processed" / "selection_analysis.csv"
    if not source.exists():
        raise FileNotFoundError(f"Missing required selection analysis: {source}")
    selection = pd.read_csv(source)
    required = {
        "AHP_State", "Total_Decisions", "NB_Sel", "5G_Sel", "Dom_NB",
        "Dom_5G", "Dom_None", "Single_Feas",
    }
    missing = required.difference(selection.columns)
    if missing:
        raise ValueError(f"Selection analysis is missing columns: {sorted(missing)}")

    by_state = selection.groupby("AHP_State", as_index=False)[
        ["Total_Decisions", "NB_Sel", "5G_Sel", "Dom_NB", "Dom_5G", "Dom_None", "Single_Feas"]
    ].sum()
    by_state["NB_Selection_Pct"] = np.where(
        by_state["Total_Decisions"] > 0,
        100 * by_state["NB_Sel"] / by_state["Total_Decisions"],
        np.nan,
    )
    by_state["5G_Selection_Pct"] = np.where(
        by_state["Total_Decisions"] > 0,
        100 * by_state["5G_Sel"] / by_state["Total_Decisions"],
        np.nan,
    )
    by_state["Single_Feasible_Pct"] = np.where(
        by_state["Total_Decisions"] > 0,
        100 * by_state["Single_Feas"] / by_state["Total_Decisions"],
        np.nan,
    )

    overall = selection[
        ["Total_Decisions", "NB_Sel", "5G_Sel", "Dom_NB", "Dom_5G", "Dom_None", "Single_Feas"]
    ].sum()
    total = int(overall["Total_Decisions"])
    overall_row = {
        "AHP_State": "OVERALL",
        **{key: int(overall[key]) for key in overall.index},
        "NB_Selection_Pct": 100 * overall["NB_Sel"] / total if total else np.nan,
        "5G_Selection_Pct": 100 * overall["5G_Sel"] / total if total else np.nan,
        "Single_Feasible_Pct": 100 * overall["Single_Feas"] / total if total else np.nan,
    }
    by_state = pd.concat([by_state, pd.DataFrame([overall_row])], ignore_index=True)

    if "Scenario" in selection.columns:
        by_scenario = selection.groupby("Scenario", as_index=False)[
            ["Total_Decisions", "NB_Sel", "5G_Sel", "Dom_NB", "Dom_5G", "Dom_None", "Single_Feas"]
        ].sum()
        by_scenario["NB_Selection_Pct"] = np.where(
            by_scenario["Total_Decisions"] > 0,
            100 * by_scenario["NB_Sel"] / by_scenario["Total_Decisions"],
            np.nan,
        )
        by_scenario["5G_Selection_Pct"] = np.where(
            by_scenario["Total_Decisions"] > 0,
            100 * by_scenario["5G_Sel"] / by_scenario["Total_Decisions"],
            np.nan,
        )
    else:
        by_scenario = pd.DataFrame()
    return by_state, by_scenario


def build_baseline_candidate_inputs() -> pd.DataFrame:
    rows = []
    ahp = DynamicAHP()
    payload_states = [
        ("NORMAL", False, 100.0, 50, 10.0),
        ("LOW_BATTERY", False, 19.0, 50, 10.0),
        ("EMERGENCY", True, 100.0, 200, 1.0),
        ("CONFLICT", True, 19.0, 200, 1.0),
    ]
    links = {
        "NB-IoT": {
            "bandwidth_bps": 66_000.0,
            "base_latency_s": 0.5,
            "setup_delay_s": 1.5,
            "setup_energy_j": 1.5,
            "tx_power_w": 1.0,
            "reliability_pct": 95.0,
        },
        "5G NR": {
            "bandwidth_bps": 100_000_000.0,
            "base_latency_s": 0.02,
            "setup_delay_s": 0.1,
            "setup_energy_j": 0.5,
            "tx_power_w": 3.0,
            "reliability_pct": 99.0,
        },
    }
    for state, is_emergency, battery, payload, deadline in payload_states:
        weights, cr = ahp.calculate_weights(ahp.matrices[state])
        for name, params in links.items():
            tx_time = payload * 8.0 / params["bandwidth_bps"]
            predicted_latency = params["setup_delay_s"] + params["base_latency_s"] + tx_time
            predicted_energy = params["setup_energy_j"] + params["tx_power_w"] * tx_time
            rows.append(
                {
                    "State": state,
                    "Packet_Type": "Emergency" if is_emergency else "Telemetry",
                    "Payload_Bytes": payload,
                    "Deadline_s": deadline,
                    "Candidate": name,
                    "Predicted_Latency_s_Initial_Sleep": predicted_latency,
                    "Instantaneous_Energy_J_Initial_Sleep": predicted_energy,
                    "Configured_Reliability_pct": params["reliability_pct"],
                    "Nominal_Bandwidth_bps": params["bandwidth_bps"],
                    "QoS_Feasible_At_Initial_Sleep": predicted_latency <= deadline,
                    "AHP_CR": cr,
                    "AHP_Weights": ", ".join(f"{value:.6f}" for value in weights),
                    "Interpretation": "Initial-sleep marginal estimate; not a horizon-average energy forecast.",
                }
            )
    return pd.DataFrame(rows)


def build_paired_fdr() -> pd.DataFrame:
    raw_path = RESULTS / "raw" / "raw_paired_metrics.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw paired data: {raw_path}")
    raw = pd.read_csv(raw_path)
    required = {"Scenario", "Algorithm", "Seed", *METRICS.keys()}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Raw result file is missing columns: {sorted(missing)}")

    rows = []
    for scenario in sorted(raw["Scenario"].unique()):
        subset = raw[raw["Scenario"] == scenario]
        ahp = subset[subset["Algorithm"] == "AHP"].set_index("Seed")
        for algorithm in sorted(subset["Algorithm"].unique()):
            if algorithm == "AHP":
                continue
            candidate = subset[subset["Algorithm"] == algorithm].set_index("Seed")
            joined = candidate.join(
                ahp[list(METRICS)].add_suffix("_AHP"),
                how="inner",
            )
            for metric, label in METRICS.items():
                pair = joined[[metric, f"{metric}_AHP"]].dropna()
                difference = pair[metric] - pair[f"{metric}_AHP"]
                summary = paired_t_summary(difference.to_numpy(dtype=float), alpha=0.05)
                n = int(summary["Valid_Pairs"])
                mean_diff = float(summary["Mean_Difference"])
                rows.append(
                    {
                        "Scenario": scenario,
                        "Algorithm": algorithm,
                        "Metric": metric,
                        "Metric_Description": label,
                        "Valid_Pairs": n,
                        "Mean_Difference_Algorithm_minus_AHP": mean_diff,
                        "Difference_SD": summary["Difference_SD"],
                        "Observed_Difference_Min": summary["Observed_Difference_Min"],
                        "Observed_Difference_Max": summary["Observed_Difference_Max"],
                        "Difference_CI95_Lower": summary["CI_Lower"],
                        "Difference_CI95_Upper": summary["CI_Upper"],
                        "Cohens_dz_Paired": summary["Cohens_dz"],
                        "T_Statistic": summary["T_Statistic"],
                        "P_Value_Unadjusted": summary["P_Value"],
                        "Wilcoxon_P_Value": summary["Wilcoxon_P_Value"],
                        "Wilcoxon_Method": summary["Wilcoxon_Method"],
                        "Shapiro_W": summary["Shapiro_W"],
                        "Shapiro_P": summary["Shapiro_P"],
                        "Inference_Status": summary["Inference_Status"],
                        "Test_Method": summary["Test_Method"],
                    }
                )

    output = pd.DataFrame(rows)
    output["P_Value_BH_FDR"] = np.nan
    output["Wilcoxon_P_Value_BH_FDR"] = np.nan
    output["FDR_Family_Size_Per_Metric"] = 0
    output["Wilcoxon_FDR_Family_Size_Per_Metric"] = 0
    for metric, indices in output.groupby("Metric").groups.items():
        family = output.loc[indices, "P_Value_Unadjusted"]
        valid = family.notna()
        if valid.any():
            q_values = benjamini_hochberg(family.loc[valid].to_numpy())
            output.loc[family.loc[valid].index, "P_Value_BH_FDR"] = q_values
            output.loc[indices, "FDR_Family_Size_Per_Metric"] = int(valid.sum())

        wilcoxon_family = output.loc[indices, "Wilcoxon_P_Value"]
        wilcoxon_valid = wilcoxon_family.notna()
        if wilcoxon_valid.any():
            wilcoxon_q = benjamini_hochberg(wilcoxon_family.loc[wilcoxon_valid].to_numpy())
            output.loc[wilcoxon_family.loc[wilcoxon_valid].index, "Wilcoxon_P_Value_BH_FDR"] = wilcoxon_q
            output.loc[indices, "Wilcoxon_FDR_Family_Size_Per_Metric"] = int(wilcoxon_valid.sum())
    output["Difference_Interpretation"] = output.apply(
        lambda row: (
            "Algorithm lower than AHP" if row["Mean_Difference_Algorithm_minus_AHP"] < 0
            else "Algorithm higher than AHP" if row["Mean_Difference_Algorithm_minus_AHP"] > 0
            else "No mean difference"
        ),
        axis=1,
    )
    return output


def validate_primary_archive() -> dict[str, int]:
    """Fail closed if the archived primary matrix or emergency-latency NA logic changes."""
    raw = pd.read_csv(RESULTS / "raw" / "raw_paired_metrics.csv")
    required = {"Scenario", "Algorithm", "Seed", "PDR", "Emerg_PDR", "Emerg_Lat_s", "Avg_Lat_s", "Total_Eng_J"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Primary CSV missing columns: {sorted(missing)}")
    duplicate_keys = int(raw.duplicated(["Scenario", "Algorithm", "Seed"]).sum())
    if len(raw) != 4320 or raw["Scenario"].nunique() != 24 or raw["Algorithm"].nunique() != 6 or raw["Seed"].nunique() != 30:
        raise AssertionError("Primary raw matrix must remain 24 configurations x 30 seeds x 6 strategies = 4,320 rows.")
    if duplicate_keys:
        raise AssertionError(f"Primary raw matrix contains {duplicate_keys} duplicate (Scenario, Algorithm, Seed) keys.")
    missing_emergency = raw["Emerg_Lat_s"].isna()
    missing_emergency_count = int(missing_emergency.sum())
    if missing_emergency_count != 60:
        raise AssertionError(f"Expected 60 undefined Emerg_Lat_s aggregates, found {missing_emergency_count}.")
    if not (raw.loc[missing_emergency, "Emerg_PDR"] == 0).all():
        raise AssertionError("An Emerg_Lat_s NA occurs in a row with non-zero emergency delivery ratio.")
    if not (raw.loc[missing_emergency, "Emerg_PDR"].notna()).all():
        raise AssertionError("Emergency delivery ratio is missing where emergency latency is undefined.")
    selection = pd.read_csv(RESULTS / "processed" / "selection_analysis.csv")
    if len(selection) != 2880 or selection.duplicated(["Scenario", "Seed", "AHP_State"]).any():
        raise AssertionError("Selection-analysis data must contain 2,880 unique (scenario, seed, state) rows.")
    decision_count = int(selection["Total_Decisions"].sum())
    if decision_count != 5_768_175:
        raise AssertionError(f"Unexpected AHP decision count: {decision_count}")
    return {
        "primary_rows": len(raw),
        "configurations": int(raw["Scenario"].nunique()),
        "seeds": int(raw["Seed"].nunique()),
        "strategies": int(raw["Algorithm"].nunique()),
        "primary_duplicate_keys": duplicate_keys,
        "emergency_latency_undefined_rows": missing_emergency_count,
        "selection_analysis_rows": len(selection),
        "ahp_ranking_invocations": decision_count,
    }


def main() -> None:
    integrity = validate_primary_archive()
    ahp = build_ahp_validation()
    state_summary, scenario_summary = build_selection_diagnostics()
    baseline_inputs = build_baseline_candidate_inputs()
    paired_fdr = build_paired_fdr()

    ahp.to_csv(TABLES / "ahp_consistency_validation.csv", index=False)
    state_summary.to_csv(TABLES / "selection_dominance_by_state.csv", index=False)
    if not scenario_summary.empty:
        scenario_summary.to_csv(TABLES / "selection_dominance_by_scenario.csv", index=False)
    baseline_inputs.to_csv(TABLES / "baseline_candidate_decision_inputs.csv", index=False)
    paired_fdr.to_csv(TABLES / "paired_statistics_bh_fdr.csv", index=False)

    # Refresh the canonical 144-row summary using the same paired-inference helper.
    processed_rows = []
    raw_primary = pd.read_csv(RESULTS / "raw" / "raw_paired_metrics.csv")
    for scenario in sorted(raw_primary["Scenario"].unique()):
        scenario_data = raw_primary[raw_primary["Scenario"] == scenario]
        ahp = scenario_data[scenario_data["Algorithm"] == "AHP"].set_index("Seed")
        for algorithm in sorted(scenario_data["Algorithm"].unique()):
            candidate = scenario_data[scenario_data["Algorithm"] == algorithm].set_index("Seed")
            joined = candidate.join(ahp[list(METRICS)].add_suffix("_AHP"), how="inner")
            row = {"Scenario": scenario, "Algorithm": algorithm}
            for metric in METRICS:
                values = pd.to_numeric(joined[metric], errors="coerce").dropna()
                row[f"{metric}_Mean"] = float(values.mean()) if len(values) else np.nan
                mean_summary = paired_t_summary(values.to_numpy(dtype=float), alpha=0.05)
                row[f"{metric}_CI"] = mean_summary["CI_Half_Width"]
                if algorithm == "AHP":
                    comparison = {
                        "Valid_Pairs": len(values),
                        "Mean_Difference": 0.0,
                        "CI_Half_Width": np.nan,
                        "T_Statistic": np.nan,
                        "P_Value": np.nan,
                        "Wilcoxon_P_Value": np.nan,
                        "Shapiro_P": np.nan,
                        "Inference_Status": "SELF_COMPARISON_NOT_TESTED",
                    }
                else:
                    differences = (
                        pd.to_numeric(joined[metric], errors="coerce")
                        - pd.to_numeric(joined[f"{metric}_AHP"], errors="coerce")
                    )
                    comparison = paired_t_summary(differences.to_numpy(dtype=float), alpha=0.05)
                row[f"{metric}_Valid_Pairs"] = comparison["Valid_Pairs"]
                row[f"{metric}_Diff_vs_AHP"] = comparison["Mean_Difference"]
                row[f"{metric}_Diff_CI"] = comparison["CI_Half_Width"]
                row[f"{metric}_T_Stat"] = comparison["T_Statistic"]
                row[f"{metric}_P_Value"] = comparison["P_Value"]
                row[f"{metric}_Wilcoxon_P_Value"] = comparison["Wilcoxon_P_Value"]
                row[f"{metric}_Shapiro_P"] = comparison["Shapiro_P"]
                row[f"{metric}_Inference_Status"] = comparison["Inference_Status"]
            processed_rows.append(row)
    pd.DataFrame(processed_rows).to_csv(RESULTS / "processed" / "paired_stats.csv", index=False)

    total = int(state_summary.loc[state_summary["AHP_State"] == "OVERALL", "Total_Decisions"].iloc[0])
    overall = state_summary[state_summary["AHP_State"] == "OVERALL"].iloc[0]
    pdr_tests = paired_fdr[paired_fdr["Metric"] == "PDR"]
    latency_tests = paired_fdr[paired_fdr["Metric"] == "Avg_Lat_s"]
    energy_tests = paired_fdr[paired_fdr["Metric"] == "Total_Eng_J"]

    raw_for_scope = pd.read_csv(RESULTS / "raw" / "raw_paired_metrics.csv")
    current_scenarios = int(raw_for_scope["Scenario"].nunique())
    has_5g_outage = "K_5G_OUTAGE" in set(raw_for_scope["Scenario"])
    supplement_meta = RESULTS / "supplementary" / "5g_outage" / "metadata.json"
    if supplement_meta.exists():
        pilot = json.loads(supplement_meta.read_text(encoding="utf-8"))
        pilot_note = (
            f" A separate supplementary 5G-outage/recovery pilot contains {pilot.get('rows', 0)} "
            f"records from {len(pilot.get('seeds', []))} seeds and six algorithms. It is stored "
            "under `results/supplementary/5g_outage/` and is not included in the primary matrix."
        )
    else:
        pilot_note = " A separate supplementary 5G-outage pilot can be generated with `python experiments/run_5g_outage_supplementary.py --seeds 5`; it is kept outside the primary matrix."
    scope_note = (
        f"The primary raw archive contains {current_scenarios} configurations and remains the "
        "original 24-configuration / 4,320-row dataset (30 seeds × six algorithms). "
        "The supplementary outage pilot is reported separately. Do not describe it as a 25th "
        "primary configuration or merge its records into the primary CSV." + pilot_note
    )

    both_feasible = int(overall["Dom_NB"] + overall["Dom_5G"] + overall["Dom_None"])
    assert both_feasible + int(overall["Single_Feas"]) == total, (
        "Pareto categories do not partition the AHP ranking-call denominator"
    )
    pareto_summary = pd.DataFrame([
        {
            "Category": "5G dominates NB-IoT",
            "Decision_Count": int(overall["Dom_5G"]),
            "Pct_of_all_AHP_calls": 100 * overall["Dom_5G"] / total,
            "Pct_of_both_feasible": 100 * overall["Dom_5G"] / both_feasible,
        },
        {
            "Category": "NB-IoT dominates 5G",
            "Decision_Count": int(overall["Dom_NB"]),
            "Pct_of_all_AHP_calls": 100 * overall["Dom_NB"] / total,
            "Pct_of_both_feasible": 100 * overall["Dom_NB"] / both_feasible,
        },
        {
            "Category": "Neither dominates",
            "Decision_Count": int(overall["Dom_None"]),
            "Pct_of_all_AHP_calls": 100 * overall["Dom_None"] / total,
            "Pct_of_both_feasible": 100 * overall["Dom_None"] / both_feasible,
        },
        {
            "Category": "Only one candidate feasible",
            "Decision_Count": int(overall["Single_Feas"]),
            "Pct_of_all_AHP_calls": 100 * overall["Single_Feas"] / total,
            "Pct_of_both_feasible": np.nan,
        },
    ])

    candidate_display = pd.DataFrame({
        "State": baseline_inputs["State"],
        "Packet / deadline": [
            f'{int(payload)} B / {deadline:g} s'
            for payload, deadline in zip(baseline_inputs["Payload_Bytes"], baseline_inputs["Deadline_s"])
        ],
        "Candidate": baseline_inputs["Candidate"],
        "Predicted latency (s; minimize)": baseline_inputs["Predicted_Latency_s_Initial_Sleep"].map(lambda x: f"{x:.6f}"),
        "Marginal energy (J; minimize)": baseline_inputs["Instantaneous_Energy_J_Initial_Sleep"].map(lambda x: f"{x:.6f}"),
        "Configured reliability (%; maximize)": baseline_inputs["Configured_Reliability_pct"].map(lambda x: f"{x:.0f}"),
        "Nominal bandwidth (bps; maximize)": baseline_inputs["Nominal_Bandwidth_bps"].map(lambda x: f"{x:,.0f}"),
        "Feasible at initial sleep": baseline_inputs["QoS_Feasible_At_Initial_Sleep"].map(lambda x: "Yes" if x else "No"),
    })

    pareto_display = pd.DataFrame({
        "Category": pareto_summary["Category"],
        "Decision count": pareto_summary["Decision_Count"].map(lambda x: f"{x:,}"),
        "% of all AHP ranking calls": pareto_summary["Pct_of_all_AHP_calls"].map(lambda x: f"{x:.2f}%"),
        "% of both-feasible calls": pareto_summary["Pct_of_both_feasible"].map(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "Not applicable"
        ),
    })

    paired_summary_rows = []
    for metric, group in paired_fdr.groupby("Metric", sort=False):
        status_counts = group["Inference_Status"].value_counts()
        paired_summary_rows.append({
            "Metric": metric,
            "Paired comparison records": len(group),
            "Estimable paired t-tests": int((group["Inference_Status"] == "ESTIMABLE_PAIRED_T_TEST").sum()),
            "Identical zero-difference pairs (not tested)": int((group["Inference_Status"] == "ZERO_VARIANCE_IDENTICAL").sum()),
            "Other non-estimable": int(len(group) - (group["Inference_Status"].isin(["ESTIMABLE_PAIRED_T_TEST", "ZERO_VARIANCE_IDENTICAL"])).sum()),
            "t-test BH family size": int(group["FDR_Family_Size_Per_Metric"].max()),
            "Wilcoxon BH family size": int(group["Wilcoxon_FDR_Family_Size_Per_Metric"].max()),
            "t-test BH q < 0.05": int((group["P_Value_BH_FDR"] < 0.05).sum()),
            "Wilcoxon BH q < 0.05": int((group["Wilcoxon_P_Value_BH_FDR"] < 0.05).sum()),
            "Shapiro p < 0.05": int((group["Shapiro_P"] < 0.05).sum()),
        })

    lines = [
        "# Reproducible Project Diagnostics",
        "",
        "This report is generated from the archived CSV outputs and the current analysis code. It does not rerun the primary SimPy simulations.",
        "",
        "## Primary Archive Integrity",
        "",
        f"The primary archive contains {integrity['primary_rows']:,} rows across {integrity['configurations']} configurations, {integrity['seeds']} seeds, and {integrity['strategies']} strategies. The (Scenario, Algorithm, Seed) key has {integrity['primary_duplicate_keys']} duplicates. The separate selection-analysis archive contains {integrity['selection_analysis_rows']:,} unique rows and {integrity['ahp_ranking_invocations']:,} ranking invocations.",
        "",
        f"`Emerg_Lat_s` is undefined in {integrity['emergency_latency_undefined_rows']} rows. All these rows have `Emerg_PDR = 0`: the simulation generated emergency traffic but delivered no emergency packets for that aggregate, so no delivered-emergency latency mean exists. This is not a zero-latency measurement and is not a missing simulation row. The undefined values are preserved rather than imputed as zero.",
        "",
        "## AHP Consistency",
        "",
        markdown_table(ahp),
        "",
        "The four matrices are generated as pairwise ratios of preselected design-weight vectors. CR is zero (within floating-point precision) by construction; this is a mathematical consistency check, not evidence that the preferences were elicited from domain experts.",
        "",
        "## Selection and Pareto-Dominance Diagnostics",
        "",
        markdown_table(state_summary),
        "",
        f"The denominator is {total:,} actual AHP ranking invocations, not all generated packets. A packet that fails the hard feasibility filter for both candidates does not invoke AHP-TOPSIS and is therefore outside this denominator. The per-call categories form an exhaustive partition: both feasible ({both_feasible:,}) plus only one feasible ({int(overall['Single_Feas']):,}) equals {total:,}.",
        "",
        markdown_table(pareto_display),
        "",
        "Pareto method: compare only calls where both candidates pass the hard QoS feasibility filter. Latency and candidate marginal energy are minimized; configured reliability and nominal bandwidth are maximized. Candidate X dominates candidate Y when X is no worse on all four criteria and strictly better on at least one. The mutually exclusive categories are 5G_DOM, NB_DOM, and NO_DOM for two-feasible calls; SINGLE_FEASIBLE is reported separately and is not a pairwise Pareto comparison. No-feasible packets are filtered before an AHP ranking call and are not represented in the selection-analysis denominator.",
        "",
        "`NO_DOM` does not mean that the candidates are equal: in these records each alternative has at least one criterion advantage. TOPSIS still selected 5G in these calls. Do not claim that 5G Pareto-dominates every individual decision.",
        "",
        "The 5G dominance rate is 83.69% of all AHP ranking invocations; equivalently, it is 96.13% of calls in which both alternatives are feasible. The 3.37% neither-dominates rate is 3.87% of two-feasible calls. These denominators answer different questions and must not be conflated.",
        "",
        "## Initial-Sleep Candidate Inputs",
        "",
        markdown_table(candidate_display),
        "",
        "The table displays the source-derived candidate values for representative packet/state pairs. Predicted latency = setup delay + base latency + serialization time. Initial-sleep marginal energy = setup energy + transmit power × serialization time. Values are model inputs/derived estimates, not physical measurements; the energy estimate represents a candidate decision at initial sleep and does not forecast future modem wake-up cycles, queue evolution, CPU energy, or the full simulation horizon. For normal/low-battery telemetry, the representative packet is 50 B with a 10 s deadline; emergency/conflict uses 200 B with a 1 s deadline.",
        "",
        "## Paired Statistical Comparisons",
        "",
        markdown_table(pd.DataFrame(paired_summary_rows)),
        "",
        "For each scenario and non-AHP strategy, the primary parametric comparison is a two-sided paired Student t-test, implemented equivalently as a one-sample t-test on per-seed differences (candidate minus AHP). Pairs are matched by scenario and seed. The 95% confidence interval is t-based; paired Cohen's dz is mean difference divided by the sample standard deviation of differences. The inferential model assumes independent seed replicates and an approximately normal distribution of paired differences. Shapiro-Wilk is included as an exploratory diagnostic, not as proof of normality.",
        "",
        "A sample with exactly zero variance in its paired differences has no estimable Student-t statistic, p-value, t-based confidence interval, or Cohen's dz. In particular, an all-zero difference vector is a descriptive identity, not a valid p=1.0 test result. These cells retain their zero mean and observed min/max but have inferential fields left blank (NaN). The same treatment is applied to constant nonzero differences. AHP-versus-AHP self-comparisons remain in the 144-row paired summary but are explicitly marked SELF_COMPARISON_NOT_TESTED.",
        "",
        "The Wilcoxon signed-rank test (two-sided; zero paired differences omitted) is supplied as a non-parametric sensitivity analysis for estimable comparisons; SciPy method=auto chooses exact or asymptotic calculation according to the data. Benjamini-Hochberg FDR adjustment is applied separately within each metric family and separately for the paired-t and Wilcoxon sensitivity p-values. Non-estimable cases are excluded from the corresponding FDR family rather than being assigned fabricated p-values.",
        "The exploratory Shapiro-Wilk diagnostic fell below 0.05 for 2 of 24 estimable PDR differences, 1 of 24 energy differences, and 0 of 24 mean-latency differences. The Wilcoxon sensitivity results remained BH-significant for all 24 estimable comparisons within each metric family. This is a sensitivity check, not a claim that the seed-level model assumptions are proven.",
        "",
        f"Per metric, {len(pdr_tests)} archived comparison rows are retained in the FDR audit inventory, but only {int((pdr_tests['Inference_Status'] == 'ESTIMABLE_PAIRED_T_TEST').sum())} paired-t p-values are estimable; {int((pdr_tests['Inference_Status'] == 'ZERO_VARIANCE_IDENTICAL').sum())} are exact identical-zero comparisons and are not inferential tests. The 144-row `paired_stats.csv` retains all six strategies, including AHP self-comparisons. The original raw primary results remain unchanged.",
        "",
        "## Reproduction",
        "",
        "Run `python experiments/audit_existing_results.py` from the project root. It reads archived raw result CSVs and regenerates `results/processed/paired_stats.csv`, diagnostic tables under `results/tables/`, and this report. It does not rerun SimPy simulations.",
        "",
        "## Scope Notes",
        "",
        scope_note,
    ]
    (RESULTS / "REPRODUCIBLE_PROJECT_DIAGNOSTICS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote audit tables:")
    for name in [
        "ahp_consistency_validation.csv",
        "selection_dominance_by_state.csv",
        "selection_dominance_by_scenario.csv",
        "baseline_candidate_decision_inputs.csv",
        "paired_statistics_bh_fdr.csv",
    ]:
        path = TABLES / name
        if path.exists():
            print(f" - {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print(f"Wrote {RESULTS / 'REPRODUCIBLE_PROJECT_DIAGNOSTICS.md'}")


if __name__ == "__main__":
    main()
