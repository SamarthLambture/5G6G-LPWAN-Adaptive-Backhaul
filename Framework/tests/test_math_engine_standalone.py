"""Fast unit tests for AHP/TOPSIS; these do not require SimPy."""

import numpy as np
import pytest

from src.core.math_engine import DynamicAHP, TOPSIS
from src.core.algorithms import AdapAHP


def test_all_project_ahp_states_have_expected_weights_and_zero_cr():
    ahp = DynamicAHP()
    for state, expected in ahp.vectors.items():
        matrix = ahp.matrices[state]
        weights, cr = ahp.calculate_weights(matrix)
        assert ahp.validate_matrix(matrix)
        assert np.allclose(weights, expected, atol=1e-12)
        assert cr == pytest.approx(0.0, abs=1e-10)
        assert np.sum(weights) == pytest.approx(1.0)


def test_ahp_supports_three_criteria_with_standard_random_index():
    ahp = DynamicAHP()
    weights = np.array([1.0, 2.0, 3.0])
    matrix = ahp._build_matrix(weights)
    calculated, cr = ahp.calculate_weights(matrix)
    assert np.allclose(calculated, weights / weights.sum())
    assert cr == pytest.approx(0.0, abs=1e-10)


def test_ahp_rejects_non_reciprocal_matrix():
    ahp = DynamicAHP()
    matrix = np.array([[1.0, 2.0], [0.4, 1.0]])
    with pytest.raises(ValueError, match="reciprocal"):
        ahp.calculate_weights(matrix)


def test_ahp_rejects_non_finite_battery_percentage():
    ahp = DynamicAHP()
    with pytest.raises(ValueError, match="finite"):
        ahp.get_state(False, float("nan"))


def test_topsis_selects_latency_best_when_other_criteria_equal():
    topsis = TOPSIS()
    matrix = np.array([[10.0, 1.0], [20.0, 1.0]])
    selected = topsis.rank_alternatives(
        matrix, np.array([0.8, 0.2]), [-1, -1], ["latency", "energy"]
    )
    assert selected == 0


def test_topsis_rejects_malformed_weight_vector():
    topsis = TOPSIS()
    matrix = np.array([[10.0, 1.0], [20.0, 2.0]])
    with pytest.raises(ValueError, match="one-dimensional"):
        topsis.rank_alternatives(
            matrix, np.array([[0.5, 0.5]]), [-1, -1], ["latency", "energy"]
        )


def test_adaptive_selector_uses_only_available_backhaul():
    algorithm = AdapAHP()
    decision_matrix = np.array(
        [[500.0, 1.5, 95.0, 66_000.0], [20.0, 10.0, 99.0, 100_000_000.0]]
    )
    # If 5G is unavailable, the caller passes only NB-IoT as feasible.
    assert algorithm.select_network([0], decision_matrix, False, 100.0) == 0
    # If NB-IoT is unavailable, the caller passes only 5G as feasible.
    assert algorithm.select_network([1], decision_matrix, False, 100.0) == 1
