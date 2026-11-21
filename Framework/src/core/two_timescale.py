"""Two-timescale gateway backhaul controller.

The controller separates a slower preferred-backhaul decision for a Poisson
arrival burst (the modem's configured idle-tail interval) from fast packet-level
QoS overrides.  Energy inputs are model estimates, not hardware measurements.

The existing simulator accounts for setup and transmit energy but does not
currently model modem idle-tail power.  Idle power therefore defaults to zero
and must be supplied explicitly to explore that omitted term.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
import json
from math import exp, isfinite, log
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class TwoTimescaleConfig:
    """Parameters for the session/packet controller.

    `initial_arrival_rate_pps` is used only until enough packet arrivals have
    been observed to estimate an inter-arrival rate.  It is not a measured
    traffic rate unless supplied from a known experiment configuration.
    """

    initial_arrival_rate_pps: float = 0.0
    arrival_rate_ewma_alpha: float = 0.2
    maximum_expected_packets: float = 10_000.0
    minimum_dwell_s: float = 2.0
    improvement_threshold: float = 0.10
    minimum_reliability_pct: float | None = None
    idle_power_w: Mapping[str, float] = field(
        default_factory=lambda: {"NB-IoT": 0.0, "5G NR": 0.0}
    )
    expected_idle_seconds_per_session: float = 0.0
    switching_energy_j: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.initial_arrival_rate_pps) or self.initial_arrival_rate_pps < 0:
            raise ValueError("initial_arrival_rate_pps must be finite and non-negative")
        if not 0 < self.arrival_rate_ewma_alpha <= 1:
            raise ValueError("arrival_rate_ewma_alpha must be in (0, 1]")
        if not isfinite(self.maximum_expected_packets) or self.maximum_expected_packets < 1:
            raise ValueError("maximum_expected_packets must be finite and at least 1")
        if not isfinite(self.minimum_dwell_s) or self.minimum_dwell_s < 0:
            raise ValueError("minimum_dwell_s must be finite and non-negative")
        if not 0 <= self.improvement_threshold < 1:
            raise ValueError("improvement_threshold must be in [0, 1)")
        if self.minimum_reliability_pct is not None and not 0 <= self.minimum_reliability_pct <= 100:
            raise ValueError("minimum_reliability_pct must be in [0, 100]")
        if not isfinite(self.expected_idle_seconds_per_session) or self.expected_idle_seconds_per_session < 0:
            raise ValueError("expected_idle_seconds_per_session must be finite and non-negative")
        if not isfinite(self.switching_energy_j) or self.switching_energy_j < 0:
            raise ValueError("switching_energy_j must be finite and non-negative")
        for name, power in self.idle_power_w.items():
            if not isfinite(float(power)) or float(power) < 0:
                raise ValueError(f"idle_power_w[{name!r}] must be finite and non-negative")


def load_two_timescale_config(path: str | Path | None = None, **overrides: Any) -> TwoTimescaleConfig:
    """Load the documented JSON configuration, with explicit overrides.

    Only dataclass fields are accepted from the JSON file; human-readable
    metadata such as ``description`` and ``notes`` is intentionally ignored.
    """
    config_path = Path(path) if path is not None else Path(__file__).with_name("two_timescale_config.json")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    allowed = {item.name for item in fields(TwoTimescaleConfig)}
    values = {key: value for key, value in payload.items() if key in allowed}
    values.update(overrides)
    return TwoTimescaleConfig(**values)


class TwoTimescaleController:
    """Technology-agnostic controller for two or more backhaul candidates.

    The controller depends on a normalized candidate-metrics contract, not on
    NB-IoT/5G-specific protocol classes. A runtime adapter supplies the metrics
    for each selectable profile. Candidate dictionaries are keyed by the same integer indices used by the
    existing simulator decision matrix. Required fields are `latency_s`,
    `tx_energy_j`, `setup_energy_due_j`, `setup_energy_j`, `reliability_pct`,
    `name`, `tail_time_s` and `modem_state`.

    Emergency packets use the lowest-latency feasible candidate as a temporary
    packet-level override; they do not silently change the session preference.
    The selector can accept additional candidate indices, but this does not
    mean an exploratory 6G profile has calibrated metrics or is enabled in the
    current SimPy model.
    Routine packets use a persistent session preference selected by estimated
    energy per packet over an expected Poisson burst.
    """

    def __init__(self, config: TwoTimescaleConfig | None = None) -> None:
        self.config = config or TwoTimescaleConfig()
        self.preferred_network: int | None = None
        self.last_preference_change_s: float | None = None
        self.last_arrival_s: float | None = None
        self.interarrival_ewma_s: float | None = None
        self.last_tail_time_s: float = 0.0
        self._burst_boundary_pending = False
        self.session_index = 0
        self.persistent_switches = 0
        self.packet_overrides = 0
        self.forced_fallbacks = 0
        self.last_decision: dict[str, Any] = {}

    def _observe_arrival(self, arrival_time_s: float) -> bool:
        """Update Poisson inter-arrival estimate; return whether a burst ended."""
        if not isfinite(arrival_time_s) or arrival_time_s < 0:
            raise ValueError("arrival_time_s must be finite and non-negative")
        burst_ended = False
        if self.last_arrival_s is not None:
            gap = arrival_time_s - self.last_arrival_s
            if gap < 0:
                raise ValueError("packet arrival timestamps must be non-decreasing")
            if gap > 0:
                alpha = self.config.arrival_rate_ewma_alpha
                self.interarrival_ewma_s = (
                    gap if self.interarrival_ewma_s is None
                    else alpha * gap + (1.0 - alpha) * self.interarrival_ewma_s
                )
                if self.last_tail_time_s > 0 and gap > self.last_tail_time_s:
                    burst_ended = True
        self.last_arrival_s = arrival_time_s
        return burst_ended

    def estimated_arrival_rate_pps(self) -> float:
        if self.interarrival_ewma_s is not None and self.interarrival_ewma_s > 0:
            return 1.0 / self.interarrival_ewma_s
        return self.config.initial_arrival_rate_pps

    def expected_packets_in_burst(self, tail_time_s: float) -> float:
        """Expected cluster size for Poisson arrivals separated by <= tail T.

        The geometric cluster size has mean exp(lambda*T). The result is
        capped to keep forecasts finite; this is a model-based expectation,
        not an observed session length.
        """
        if not isfinite(tail_time_s) or tail_time_s < 0:
            raise ValueError("tail_time_s must be finite and non-negative")
        rate = self.estimated_arrival_rate_pps()
        if rate <= 0 or tail_time_s == 0:
            return 1.0
        exponent = min(rate * tail_time_s, log(self.config.maximum_expected_packets))
        return min(self.config.maximum_expected_packets, max(1.0, exp(exponent)))

    def _energy_cost_per_packet(
        self,
        candidate: Mapping[str, Any],
        network_index: int,
        expected_packets: float,
        switching: bool,
    ) -> float:
        name = str(candidate["name"])
        tx_energy = float(candidate["tx_energy_j"])
        setup_due = float(candidate["setup_energy_due_j"])
        idle_power = float(self.config.idle_power_w.get(name, 0.0))
        if not all(isfinite(v) and v >= 0 for v in (tx_energy, setup_due, idle_power)):
            raise ValueError(f"Invalid energy component for candidate {name}")
        setup_energy = float(candidate.get("setup_energy_j", setup_due))
        if not isfinite(setup_energy) or setup_energy < 0:
            raise ValueError(f"Invalid setup energy for candidate {name}")
        # setup_due_j is nonzero only when the modem is currently asleep.
        # Existing BackhaulModem does not expose idle-tail power; the optional
        # configured term remains zero unless explicitly supplied.
        idle_energy = idle_power * self.config.expected_idle_seconds_per_session
        switch_energy = self.config.switching_energy_j if switching else 0.0
        return (setup_due + expected_packets * tx_energy + idle_energy + switch_energy) / expected_packets

    def select_network_with_context(
        self,
        feasible: Sequence[int],
        decision_matrix: Any,
        is_emergency: bool,
        battery_pct: float,
        *,
        arrival_time_s: float,
        now_s: float,
        candidates: Mapping[int, Mapping[str, Any]],
    ) -> int:
        """Select a feasible candidate using packet and session timescales."""
        if not isfinite(battery_pct) or not 0 <= battery_pct <= 100:
            raise ValueError("battery_pct must be finite and in [0, 100]")
        if not isfinite(now_s) or now_s < 0:
            raise ValueError("now_s must be finite and non-negative")
        matrix = decision_matrix
        if getattr(matrix, "ndim", None) != 2 or matrix.shape[1] < 2:
            raise ValueError("decision_matrix must be a 2-D matrix with latency and energy columns")
        candidate_indices = [int(i) for i in feasible if int(i) in candidates]
        if candidate_indices and max(candidate_indices) >= matrix.shape[0]:
            raise ValueError("decision_matrix must contain a row for every feasible candidate index")

        candidate_profile_ids = {
            str(int(index)): str(candidate.get("profile_id", candidate.get("name", index)))
            for index, candidate in candidates.items()
        }
        burst_ended = self._observe_arrival(arrival_time_s)
        if burst_ended:
            self._burst_boundary_pending = True
        available = [
            int(i) for i in feasible
            if int(i) in candidates and bool(candidates[int(i)].get("available", True))
        ]
        if not available:
            self.last_decision = {
                "selected_network": -1, "preferred_network": self.preferred_network,
                "decision_mode": "no_feasible_candidate", "reason": "No QoS-feasible available candidate",
                "expected_packets_per_burst": None, "candidate_costs_j_per_packet": {},
                "candidate_profile_ids": candidate_profile_ids,
            }
            return -1

        for index in available:
            candidate = candidates[index]
            for key in ("latency_s", "tx_energy_j", "setup_energy_due_j", "setup_energy_j", "tail_time_s"):
                value = float(candidate[key])
                if not isfinite(value) or value < 0:
                    raise ValueError(f"Candidate {index} has invalid {key}: {value}")
            reliability = float(candidate["reliability_pct"])
            if not isfinite(reliability) or not 0 <= reliability <= 100:
                raise ValueError(f"Candidate {index} has invalid reliability_pct: {reliability}")
            if float(candidate["setup_energy_due_j"]) > float(candidate["setup_energy_j"]) + 1e-12:
                raise ValueError(f"Candidate {index} setup energy due exceeds configured setup energy")

        # Optional reliability constraint is explicit and disabled by default.
        if self.config.minimum_reliability_pct is not None:
            reliability_feasible = [
                i for i in available
                if float(candidates[i]["reliability_pct"]) >= self.config.minimum_reliability_pct
            ]
            available = reliability_feasible
            if not available:
                self.last_decision = {
                    "selected_network": -1, "preferred_network": self.preferred_network,
                    "decision_mode": "reliability_rejection",
                    "reason": "All deadline-feasible candidates fail the configured reliability threshold",
                    "expected_packets_per_burst": None, "candidate_costs_j_per_packet": {},
                    "candidate_profile_ids": candidate_profile_ids,
                }
                return -1

        if is_emergency:
            selected = min(
                available,
                key=lambda i: (
                    float(candidates[i]["latency_s"]),
                    -float(candidates[i]["reliability_pct"]),
                    float(candidates[i]["tx_energy_j"]),
                ),
            )
            override = self.preferred_network is not None and selected != self.preferred_network
            if override:
                self.packet_overrides += 1
            self.last_decision = {
                "selected_network": selected,
                "selected_profile_id": candidate_profile_ids.get(str(selected)),
                "preferred_network": self.preferred_network,
                "preferred_profile_id": candidate_profile_ids.get(str(self.preferred_network)) if self.preferred_network is not None else None,
                "candidate_profile_ids": candidate_profile_ids,
                "decision_mode": "packet_qos_override" if override else "emergency_fastest_feasible",
                "reason": "Emergency packet uses the lowest-latency feasible backhaul; session preference is unchanged",
                "expected_packets_per_burst": None,
                "candidate_costs_j_per_packet": {},
                "packet_override": bool(override),
                "persistent_switch": False,
                "gateway_battery_pct": float(battery_pct),
            }
            return selected

        if self._burst_boundary_pending or self.preferred_network is None:
            self.session_index += 1
            session_start = True
        else:
            session_start = False

        per_candidate_packets: dict[int, float] = {}
        costs: dict[int, float] = {}
        for i in available:
            tail = float(candidates[i].get("tail_time_s", 0.0))
            n_packets = self.expected_packets_in_burst(tail)
            per_candidate_packets[i] = n_packets
            costs[i] = self._energy_cost_per_packet(
                candidates[i], i, n_packets, switching=(self.preferred_network is not None and i != self.preferred_network)
            )

        old_preference = self.preferred_network
        preferred_is_feasible = old_preference in available if old_preference is not None else True
        mode = "session_start" if session_start else "session_hold"
        reason = "Lowest estimated session energy per packet among feasible candidates"

        if not preferred_is_feasible:
            selected_preference = min(available, key=lambda i: (costs[i], float(candidates[i]["latency_s"])))
            mode = "forced_feasibility_fallback"
            reason = "Previous session preference is unavailable or violates packet QoS"
            self.forced_fallbacks += 1
        elif session_start:
            candidate_preference = min(available, key=lambda i: (costs[i], float(candidates[i]["latency_s"])))
            if old_preference is not None and candidate_preference != old_preference:
                dwell_satisfied = (
                    self.last_preference_change_s is None
                    or now_s - self.last_preference_change_s >= self.config.minimum_dwell_s
                )
                materially_better = costs[candidate_preference] <= costs[old_preference] * (1.0 - self.config.improvement_threshold)
                if dwell_satisfied and materially_better:
                    selected_preference = candidate_preference
                    mode = "session_reoptimization"
                    reason = "New burst offers a material session-energy advantage and dwell time has elapsed"
                else:
                    selected_preference = old_preference
                    mode = "session_boundary_hold"
                    reason = "Previous preference retained because dwell-time or improvement threshold is not satisfied"
            else:
                selected_preference = candidate_preference
        else:
            selected_preference = old_preference
            challengers = [i for i in available if i != old_preference]
            if challengers:
                challenger = min(challengers, key=lambda i: (costs[i], float(candidates[i]["latency_s"])))
                current_cost = costs[old_preference]
                challenger_cost = costs[challenger]
                dwell_satisfied = (
                    self.last_preference_change_s is None
                    or now_s - self.last_preference_change_s >= self.config.minimum_dwell_s
                )
                materially_better = challenger_cost <= current_cost * (1.0 - self.config.improvement_threshold)
                if dwell_satisfied and materially_better:
                    selected_preference = challenger
                    mode = "session_reoptimization"
                    reason = "Alternative has a material estimated session-energy advantage and dwell time has elapsed"

        persistent_switch = old_preference is not None and selected_preference != old_preference
        if persistent_switch:
            self.persistent_switches += 1
        if old_preference is None or persistent_switch:
            self.last_preference_change_s = now_s
        self.preferred_network = selected_preference
        self.last_tail_time_s = float(candidates[selected_preference].get("tail_time_s", 0.0))
        self._burst_boundary_pending = False

        self.last_decision = {
            "selected_network": selected_preference,
            "selected_profile_id": candidate_profile_ids.get(str(selected_preference)),
            "preferred_network": self.preferred_network,
            "preferred_profile_id": candidate_profile_ids.get(str(self.preferred_network)),
            "candidate_profile_ids": candidate_profile_ids,
            "decision_mode": mode,
            "reason": reason,
            "session_index": self.session_index,
            "expected_packets_per_burst": per_candidate_packets.get(selected_preference, 1.0),
            "candidate_expected_packets": {str(i): v for i, v in per_candidate_packets.items()},
            "candidate_costs_j_per_packet": {str(i): v for i, v in costs.items()},
            "persistent_switch": bool(persistent_switch),
            "packet_override": False,
            "estimated_arrival_rate_pps": self.estimated_arrival_rate_pps(),
            "gateway_battery_pct": float(battery_pct),
        }
        return selected_preference

    def select_network(self, feasible: Sequence[int], decision_matrix: Any, is_emergency: bool, battery_pct: float) -> int:
        """Compatibility API for callers without modem-state context.

        Since the matrix's energy column already includes the current marginal
        estimate, it is treated as an all-in per-packet value (no additional
        setup amortization is applied). The integrated SimPy gateway uses
        `select_network_with_context` for the full two-timescale behaviour.
        """
        if not feasible:
            return -1
        available = list(feasible)
        if is_emergency:
            return min(available, key=lambda i: float(decision_matrix[i, 0]))
        if self.preferred_network in available:
            return int(self.preferred_network)
        selected = min(available, key=lambda i: (float(decision_matrix[i, 1]), float(decision_matrix[i, 0])))
        self.preferred_network = int(selected)
        return int(selected)

    def get_ahp_state(self, is_emergency: bool, battery_pct: float) -> str:
        if is_emergency and battery_pct < 20:
            return "CONFLICT"
        if is_emergency:
            return "EMERGENCY"
        if battery_pct < 20:
            return "LOW_BATTERY"
        return "NORMAL"
