"""AHP and TOPSIS utilities used by the edge-gateway selector.

The project currently uses four criteria (latency, energy, reliability,
bandwidth).  The Random Index table below also makes the consistency-ratio
calculation explicit if the matrix dimension is changed in future work.
"""

import numpy as np


class DynamicAHP:
    # Saaty Random Index values commonly used for consistency-ratio checks.
    # RI is zero for n=1 or n=2; n=2 reciprocal matrices are always consistent.
    RANDOM_INDEX = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49,
    }

    def __init__(self):
        # Criteria: [Latency, Energy, Reliability, Bandwidth]
        self.vectors = {
            "NORMAL": np.array([2 / 13, 6 / 13, 2 / 13, 3 / 13], dtype=float),
            "EMERGENCY": np.array([4 / 8, 1 / 8, 2 / 8, 1 / 8], dtype=float),
            "LOW_BATTERY": np.array([1 / 8, 5 / 8, 1 / 8, 1 / 8], dtype=float),
            "CONFLICT": np.array([4 / 11, 4 / 11, 2 / 11, 1 / 11], dtype=float),
        }
        self.matrices = {key: self._build_matrix(vector) for key, vector in self.vectors.items()}
        # The state matrices are fixed design inputs. Cache their validated
        # priority vectors/CR once rather than solving the same eigenproblem
        # for every packet decision.
        self._state_weight_cache = {}

    @staticmethod
    def _build_matrix(weights):
        weights = np.asarray(weights, dtype=float)
        if weights.ndim != 1 or weights.size == 0:
            raise ValueError("AHP weights must be a non-empty one-dimensional vector.")
        if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
            raise ValueError("AHP weights must be finite and strictly positive.")
        weights = weights / weights.sum()
        return weights[:, None] / weights[None, :]

    def validate_matrix(self, matrix):
        if not isinstance(matrix, np.ndarray):
            raise TypeError("AHP comparison matrix must be a NumPy array.")
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0:
            raise ValueError("AHP comparison matrix must be a non-empty square matrix.")
        if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0):
            raise ValueError("AHP matrix entries must be finite and strictly positive.")
        if not np.allclose(np.diag(matrix), 1.0, rtol=0.0, atol=1e-10):
            raise ValueError("AHP comparison-matrix diagonal must equal 1.")
        if not np.allclose(matrix * matrix.T, 1.0, rtol=1e-8, atol=1e-10):
            raise ValueError("AHP comparison matrix must be reciprocal.")
        if matrix.shape[0] not in self.RANDOM_INDEX:
            raise ValueError(
                f"AHP consistency ratio is supported for matrix sizes 1-10; got n={matrix.shape[0]}."
            )
        return True

    def calculate_weights(self, matrix):
        """Return the geometric-mean priority vector and AHP consistency ratio."""
        self.validate_matrix(matrix)
        n = matrix.shape[0]

        geom_mean = np.exp(np.mean(np.log(matrix), axis=1))
        weight_sum = float(np.sum(geom_mean))
        if not np.isfinite(weight_sum) or weight_sum <= 0:
            raise ValueError("Unable to normalize AHP priority vector.")
        weights = geom_mean / weight_sum

        # Use the principal eigenvalue for the consistency calculation.
        eigenvalues = np.linalg.eigvals(matrix)
        lambda_max = float(np.max(eigenvalues.real))
        ci = max(0.0, (lambda_max - n) / (n - 1)) if n > 1 else 0.0
        ri = self.RANDOM_INDEX[n]
        if ri == 0.0:
            cr = 0.0 if ci <= 1e-10 else float("inf")
        else:
            cr = ci / ri

        if cr > 0.10:
            raise ValueError(f"AHP consistency ratio {cr:.4f} exceeds the 0.10 threshold.")
        return weights, cr

    def get_state(self, is_emerg, batt_pct):
        if not np.isfinite(batt_pct) or not (0.0 <= batt_pct <= 100.0):
            raise ValueError("Battery percentage must be finite and between 0 and 100.")
        if is_emerg and batt_pct < 20.0:
            return "CONFLICT"
        if is_emerg:
            return "EMERGENCY"
        if batt_pct < 20.0:
            return "LOW_BATTERY"
        return "NORMAL"

    def get_state_matrix(self, is_emerg, batt_pct):
        state = self.get_state(is_emerg, batt_pct)
        return self.matrices[state]

    def get_state_weights(self, is_emerg, batt_pct):
        """Return cached AHP weights and CR for the current operating state."""
        state = self.get_state(is_emerg, batt_pct)
        if state not in self._state_weight_cache:
            self._state_weight_cache[state] = self.calculate_weights(self.matrices[state])
        weights, consistency_ratio = self._state_weight_cache[state]
        return weights.copy(), consistency_ratio


class TOPSIS:
    def rank_alternatives(self, decision_matrix, weights, criteria_types, criteria_names):
        if not isinstance(decision_matrix, np.ndarray):
            raise TypeError("Decision matrix must be a NumPy array.")
        if decision_matrix.ndim != 2:
            raise ValueError("Decision matrix must be two-dimensional.")
        if decision_matrix.shape[0] == 0:
            return -1
        if decision_matrix.shape[1] == 0:
            raise ValueError("Decision matrix must contain at least one criterion.")

        weights = np.asarray(weights, dtype=float)
        criteria_types = list(criteria_types)
        criteria_names = list(criteria_names)
        n_criteria = decision_matrix.shape[1]

        if weights.ndim != 1 or weights.size != n_criteria:
            raise ValueError("Weights must be a one-dimensional vector matching the criteria count.")
        if len(criteria_types) != n_criteria or len(criteria_names) != n_criteria:
            raise ValueError("Decision matrix, weights, criterion types, and names must align.")
        if not np.all(np.isfinite(weights)) or np.any(weights < 0):
            raise ValueError("Weights must be finite and non-negative.")
        if not np.isclose(np.sum(weights), 1.0, rtol=0.0, atol=1e-8):
            raise ValueError("Weights must sum to 1.")
        if any(criterion not in (-1, 1) for criterion in criteria_types):
            raise ValueError("Criterion direction must be -1 (cost) or +1 (benefit).")

        if decision_matrix.shape[0] == 1:
            return 0

        if not np.all(np.isfinite(decision_matrix)) or np.any(decision_matrix < 0):
            raise ValueError("Decision matrix values must be finite and non-negative.")

        matrix = decision_matrix.astype(float, copy=False)
        norm_denominator = np.sqrt(np.sum(matrix ** 2, axis=0))
        normalized = np.divide(
            matrix,
            norm_denominator,
            out=np.zeros_like(matrix, dtype=float),
            where=norm_denominator > 0,
        )
        weighted = normalized * weights

        ideal_best = np.zeros(n_criteria, dtype=float)
        ideal_worst = np.zeros(n_criteria, dtype=float)
        for j, direction in enumerate(criteria_types):
            if direction == 1:
                ideal_best[j] = np.max(weighted[:, j])
                ideal_worst[j] = np.min(weighted[:, j])
            else:
                ideal_best[j] = np.min(weighted[:, j])
                ideal_worst[j] = np.max(weighted[:, j])

        distance_best = np.sqrt(np.sum((weighted - ideal_best) ** 2, axis=1))
        distance_worst = np.sqrt(np.sum((weighted - ideal_worst) ** 2, axis=1))
        denominator = distance_best + distance_worst
        closeness = np.divide(
            distance_worst,
            denominator,
            out=np.full_like(distance_worst, 0.5),
            where=denominator > 0,
        )

        best_indices = np.flatnonzero(np.isclose(closeness, np.max(closeness)))
        if len(best_indices) > 1:
            # Deterministic tie-break: choose the candidate with lower energy.
            energy_index = next(
                (idx for idx, name in enumerate(criteria_names) if str(name).lower() == "energy"),
                None,
            )
            if energy_index is not None:
                return int(best_indices[np.argmin(matrix[best_indices, energy_index])])
        return int(best_indices[0])
