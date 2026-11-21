import math

import numpy as np
import pytest

from src.core.paired_statistics import paired_t_summary


def test_non_degenerate_paired_differences_return_inference_and_ci():
    result = paired_t_summary([1, 2, 3, 4, 5])
    assert result["Valid_Pairs"] == 5
    assert result["Inference_Status"] == "ESTIMABLE_PAIRED_T_TEST"
    assert result["T_Statistic"] > 0
    assert 0 <= result["P_Value"] <= 1
    assert result["CI_Lower"] < result["Mean_Difference"] < result["CI_Upper"]
    assert result["Cohens_dz"] == pytest.approx(3 / np.std([1, 2, 3, 4, 5], ddof=1))
    assert math.isfinite(result["Shapiro_P"])
    assert math.isfinite(result["Wilcoxon_P_Value"])


def test_identical_zero_differences_do_not_receive_fabricated_p_value():
    result = paired_t_summary([0, 0, 0, 0])
    assert result["Mean_Difference"] == 0
    assert result["Inference_Status"] == "ZERO_VARIANCE_IDENTICAL"
    assert math.isnan(result["T_Statistic"])
    assert math.isnan(result["P_Value"])
    assert math.isnan(result["CI_Lower"])
    assert math.isnan(result["CI_Upper"])
    assert math.isnan(result["Cohens_dz"])
    assert math.isnan(result["Wilcoxon_P_Value"])


def test_constant_nonzero_differences_are_not_given_degenerate_inference():
    result = paired_t_summary([2, 2, 2, 2])
    assert result["Mean_Difference"] == 2
    assert result["Inference_Status"] == "ZERO_VARIANCE_CONSTANT_NONZERO"
    assert math.isnan(result["P_Value"])
    assert math.isnan(result["CI_Half_Width"])


def test_nonfinite_differences_are_omitted_and_single_pair_is_not_tested():
    result = paired_t_summary([float("nan"), 3.0, float("inf")])
    assert result["Valid_Pairs"] == 1
    assert result["Mean_Difference"] == 3.0
    assert result["Inference_Status"] == "INSUFFICIENT_PAIRS"
    assert math.isnan(result["P_Value"])


def test_invalid_alpha_is_rejected():
    with pytest.raises(ValueError):
        paired_t_summary([1, 2, 3], alpha=1.0)
