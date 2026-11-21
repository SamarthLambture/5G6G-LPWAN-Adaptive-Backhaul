"""Shared, explicit paired-sample inference helpers.

A zero sample standard deviation makes the conventional paired Student-t
statistic non-estimable. We retain descriptive differences but do not invent
p-values, confidence intervals, or standardized effects for that case.
"""
from __future__ import annotations

from typing import Iterable
import numpy as np
from scipy import stats


def paired_t_summary(differences: Iterable[float], alpha: float = 0.05) -> dict[str, float | int | str]:
    """Summarize paired differences using a two-sided one-sample t procedure.

    Non-finite differences are omitted. Inferential fields are NaN when fewer
    than two pairs are available or sample variance is zero. Shapiro-Wilk is
    reported as an exploratory diagnostic for estimable samples with 3..5000
    observations; it does not establish normality.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")

    values = np.asarray(list(differences), dtype=float)
    if values.ndim != 1:
        raise ValueError("differences must be one-dimensional")
    values = values[np.isfinite(values)]
    n = int(values.size)

    nan = float("nan")
    mean = float(np.mean(values)) if n else nan
    sd = float(np.std(values, ddof=1)) if n > 1 else nan
    min_value = float(np.min(values)) if n else nan
    max_value = float(np.max(values)) if n else nan

    result: dict[str, float | int | str] = {
        "Valid_Pairs": n,
        "Mean_Difference": mean,
        "Difference_SD": sd,
        "Observed_Difference_Min": min_value,
        "Observed_Difference_Max": max_value,
        "CI_Alpha": float(alpha),
        "CI_Lower": nan,
        "CI_Upper": nan,
        "CI_Half_Width": nan,
        "T_Statistic": nan,
        "P_Value": nan,
        "Wilcoxon_P_Value": nan,
        "Wilcoxon_Method": "Not run: zero variance or insufficient pairs",
        "Cohens_dz": nan,
        "Shapiro_W": nan,
        "Shapiro_P": nan,
        "Inference_Status": "INSUFFICIENT_PAIRS" if n < 2 else "NOT_EVALUATED",
        "Test_Method": "Two-sided paired Student t-test (one-sample t-test on paired differences)",
    }

    if n < 2:
        return result

    if not np.isfinite(sd) or sd == 0.0:
        result["Inference_Status"] = (
            "ZERO_VARIANCE_IDENTICAL" if mean == 0.0 else "ZERO_VARIANCE_CONSTANT_NONZERO"
        )
        return result

    df = n - 1
    half_width = float(stats.t.ppf(1.0 - alpha / 2.0, df) * sd / np.sqrt(n))
    t_result = stats.ttest_1samp(values, popmean=0.0, alternative="two-sided")
    result.update(
        {
            "CI_Lower": mean - half_width,
            "CI_Upper": mean + half_width,
            "CI_Half_Width": half_width,
            "T_Statistic": float(t_result.statistic),
            "P_Value": float(t_result.pvalue),
            "Cohens_dz": mean / sd,
            "Inference_Status": "ESTIMABLE_PAIRED_T_TEST",
        }
    )
    if 3 <= n <= 5000:
        shapiro = stats.shapiro(values)
        result["Shapiro_W"] = float(shapiro.statistic)
        result["Shapiro_P"] = float(shapiro.pvalue)
    # Non-parametric sensitivity check. SciPy's auto mode uses an exact or
    # asymptotic calculation depending on sample size/ties/zeros.
    try:
        wilcoxon = stats.wilcoxon(
            values,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )
        result["Wilcoxon_P_Value"] = float(wilcoxon.pvalue)
        result["Wilcoxon_Method"] = (
            "Wilcoxon signed-rank, two-sided; zero differences omitted; "
            "SciPy method=auto (exact or asymptotic as applicable)"
        )
    except ValueError as exc:
        result["Wilcoxon_Method"] = f"Not estimable: {exc}"
    return result
