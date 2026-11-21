"""Standalone tests for result-audit statistics; no SimPy required."""

import numpy as np
import pytest

from experiments.audit_existing_results import benjamini_hochberg


def test_benjamini_hochberg_known_example():
    p_values = np.array([0.01, 0.04, 0.03, 0.002])
    q_values = benjamini_hochberg(p_values)
    assert np.allclose(q_values, np.array([0.02, 0.04, 0.04, 0.008]))


def test_benjamini_hochberg_preserves_order_and_bounds():
    p_values = np.array([0.9, 0.001, 0.2, 0.01])
    q_values = benjamini_hochberg(p_values)
    assert q_values.shape == p_values.shape
    assert np.all(q_values >= p_values)
    assert np.all((q_values >= 0) & (q_values <= 1))


def test_benjamini_hochberg_rejects_invalid_values():
    with pytest.raises(ValueError):
        benjamini_hochberg(np.array([0.1, np.nan]))
