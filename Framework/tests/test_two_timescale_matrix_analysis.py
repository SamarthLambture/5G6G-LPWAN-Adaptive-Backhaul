import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "analyze_two_timescale_matrix.py"
spec = importlib.util.spec_from_file_location("analyze_two_timescale_matrix", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_holm_adjustment_is_monotone_in_sorted_p_values():
    adjusted = module.holm_adjust([0.04, 0.001, 0.02])
    assert len(adjusted) == 3
    assert all(0 <= value <= 1 for value in adjusted)
    by_raw = sorted(zip([0.04, 0.001, 0.02], adjusted))
    assert [value for _, value in by_raw] == sorted(value for _, value in by_raw)


def test_analyze_pairs_by_condition_and_seed():
    rows = []
    for condition, rate in [("low", 0.5), ("high", 4.0)]:
        for seed in range(5):
            base = 0.5 + seed * 0.01
            proposed = base - (0.05 if condition == "low" else 0.01)
            for algorithm, latency in [(module.BASELINE, base), (module.PROPOSED, proposed)]:
                rows.append({
                    "Condition_ID": condition,
                    "Offered_Load_pps": rate,
                    "Emergency_Ratio": 0.1,
                    "Outage_Pattern": "none",
                    "Seed": seed,
                    "Algorithm": algorithm,
                    "PDR": 0.95,
                    "Mean_Latency_s": latency,
                    "P95_Latency_s": latency * 2,
                    "Emergency_PDR": 0.8,
                    "Total_Modelled_Energy_J": 1.0,
                    "Mean_Decision_Time_us": 50.0 if algorithm == module.PROPOSED else 200.0,
                })
    result = module.analyze(pd.DataFrame(rows))
    assert len(result) == 2 * len(module.METRICS)
    latency = result[result.Metric == "Mean_Latency_s"]
    assert set(latency.Condition_ID) == {"low", "high"}
    assert (latency.Paired_Difference_TSC_Minus_Baseline < 0).all()
    assert (result.Wilcoxon_P_Holm_All_Conditions >= result.Wilcoxon_P_Raw).all()
