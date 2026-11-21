import math

import numpy as np
import pytest

from src.core.two_timescale import TwoTimescaleConfig, TwoTimescaleController, load_two_timescale_config


def context(
    name, *, latency, tx, setup, state="ACTIVE", reliability=99.0, tail=2.0
):
    return {
        "name": name,
        "modem_state": state,
        "available": True,
        "latency_s": float(latency),
        "reliability_pct": float(reliability),
        "bandwidth_bps": 1_000_000.0,
        "tx_time_s": 0.001,
        "tx_energy_j": float(tx),
        "setup_energy_j": float(setup),
        "setup_energy_due_j": float(setup if state == "SLEEP" else 0.0),
        "tail_time_s": float(tail),
    }


def inputs(candidates):
    matrix = np.array([
        [candidates[0]["latency_s"], candidates[0]["tx_energy_j"]],
        [candidates[1]["latency_s"], candidates[1]["tx_energy_j"]],
    ])
    return [i for i, c in candidates.items() if c.get("available", True)], matrix


def call(controller, candidates, *, emergency=False, arrival=0.0, now=0.0, battery=100.0):
    feasible, matrix = inputs(candidates)
    return controller.select_network_with_context(
        feasible, matrix, emergency, battery,
        arrival_time_s=arrival, now_s=now, candidates=candidates,
    )


def test_expected_packets_poisson_cluster_estimate():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    assert controller.expected_packets_in_burst(2.0) == pytest.approx(math.exp(4.0))


def test_expected_packets_learns_arrival_rate_from_interarrival_ewma():
    controller = TwoTimescaleController(TwoTimescaleConfig(arrival_rate_ewma_alpha=1.0))
    controller._observe_arrival(0.0)
    controller._observe_arrival(0.5)
    assert controller.estimated_arrival_rate_pps() == pytest.approx(2.0)
    assert controller.expected_packets_in_burst(2.0) == pytest.approx(math.exp(4.0))


def test_session_cost_amortizes_setup_and_uses_modem_state():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    n = controller.expected_packets_in_burst(2.0)
    nb_active = context("NB-IoT", latency=2.0, tx=0.0061, setup=1.5, state="ACTIVE")
    g5_sleep = context("5G NR", latency=0.12, tx=0.000012, setup=0.5, state="SLEEP")
    nb_cost = controller._energy_cost_per_packet(nb_active, 0, n, False)
    g5_cost = controller._energy_cost_per_packet(g5_sleep, 1, n, False)
    assert nb_cost == pytest.approx(0.0061)
    assert g5_cost == pytest.approx(0.5 / n + 0.000012)
    assert nb_cost < g5_cost


def test_first_routine_session_chooses_lowest_session_energy_candidate():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.0061, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.000012, setup=0.5, state="SLEEP"),
    }
    assert call(controller, candidates) == 0
    assert controller.last_decision["decision_mode"] == "session_start"
    assert controller.preferred_network == 0


def test_both_sleep_prefers_lower_amortized_setup_cost_5g():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.0061, setup=1.5, state="SLEEP"),
        1: context("5G NR", latency=0.12, tx=0.000012, setup=0.5, state="SLEEP"),
    }
    assert call(controller, candidates) == 1


def test_emergency_uses_lowest_latency_without_changing_session_preference():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    routine = {
        0: context("NB-IoT", latency=2.0, tx=0.0061, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.000012, setup=0.5, state="SLEEP"),
    }
    assert call(controller, routine) == 0
    emergency = {
        0: context("NB-IoT", latency=2.024, tx=0.024, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.120, tx=0.000048, setup=0.5, state="SLEEP"),
    }
    assert call(controller, emergency, emergency=True, arrival=0.5, now=0.505) == 1
    assert controller.preferred_network == 0
    assert controller.last_decision["packet_override"] is True
    assert controller.last_decision["persistent_switch"] is False
    assert controller.packet_overrides == 1


def test_preferred_network_infeasible_forces_fallback_even_during_dwell():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0, minimum_dwell_s=100))
    both = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    assert call(controller, both) == 0
    only_5g = {0: both[0], 1: dict(both[1], available=True)}
    feasible = [1]
    matrix = np.array([[2.0, 0.006], [0.12, 0.00001]])
    selected = controller.select_network_with_context(
        feasible, matrix, False, 100.0, arrival_time_s=0.5, now_s=0.5, candidates=only_5g
    )
    assert selected == 1
    assert controller.last_decision["decision_mode"] == "forced_feasibility_fallback"
    assert controller.forced_fallbacks == 1
    assert controller.persistent_switches == 1


def test_dwell_time_prevents_switch_until_elapsed():
    controller = TwoTimescaleController(TwoTimescaleConfig(
        initial_arrival_rate_pps=2.0, minimum_dwell_s=10.0, improvement_threshold=0.10
    ))
    first = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    assert call(controller, first) == 0
    challenger_better = {
        0: context("NB-IoT", latency=2.0, tx=0.05, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="ACTIVE"),
    }
    assert call(controller, challenger_better, arrival=0.5, now=1.0) == 0
    assert controller.last_decision["decision_mode"] == "session_hold"
    assert call(controller, challenger_better, arrival=1.0, now=11.0) == 1
    assert controller.last_decision["decision_mode"] == "session_reoptimization"
    assert controller.persistent_switches == 1


def test_arrival_gap_longer_than_tail_starts_new_session():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="SLEEP"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    call(controller, candidates, arrival=0.0, now=0.0)
    old_session = controller.session_index
    call(controller, candidates, arrival=3.0, now=3.0)
    assert controller.session_index == old_session + 1
    assert controller.last_decision["decision_mode"] == "session_start"


def test_optional_reliability_threshold_can_reject_candidates():
    controller = TwoTimescaleController(TwoTimescaleConfig(minimum_reliability_pct=99.5))
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE", reliability=95),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="ACTIVE", reliability=99),
    }
    assert call(controller, candidates) == -1
    assert controller.last_decision["decision_mode"] == "reliability_rejection"


def test_no_feasible_candidates_returns_minus_one():
    controller = TwoTimescaleController()
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5),
    }
    matrix = np.zeros((2, 2))
    assert controller.select_network_with_context(
        [], matrix, False, 100, arrival_time_s=0, now_s=0, candidates=candidates
    ) == -1


def test_optional_idle_power_is_explicit_in_session_cost():
    controller = TwoTimescaleController(TwoTimescaleConfig(
        initial_arrival_rate_pps=2.0,
        idle_power_w={"NB-IoT": 0.01, "5G NR": 0.02},
        expected_idle_seconds_per_session=5.0,
    ))
    n = 10.0
    nb = context("NB-IoT", latency=2.0, tx=0.01, setup=1.5, state="ACTIVE")
    cost = controller._energy_cost_per_packet(nb, 0, n, False)
    assert cost == pytest.approx(0.015)


def test_invalid_configuration_rejected():
    with pytest.raises(ValueError):
        TwoTimescaleConfig(improvement_threshold=1.0)
    with pytest.raises(ValueError):
        TwoTimescaleConfig(minimum_dwell_s=-1)


def test_emergency_after_burst_boundary_does_not_lose_next_session_reoptimization():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=2.0))
    routine = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    call(controller, routine, arrival=0.0, now=0.0)
    first_session = controller.session_index
    emergency = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    call(controller, emergency, emergency=True, arrival=3.0, now=3.0)
    assert controller.session_index == first_session
    assert controller._burst_boundary_pending is True
    call(controller, routine, arrival=3.2, now=3.2)
    assert controller.session_index == first_session + 1
    assert controller.last_decision["decision_mode"] == "session_start"


def test_new_burst_does_not_bypass_switch_dwell_or_improvement_threshold():
    controller = TwoTimescaleController(TwoTimescaleConfig(
        initial_arrival_rate_pps=2.0, minimum_dwell_s=10.0, improvement_threshold=0.10
    ))
    first = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="SLEEP"),
    }
    assert call(controller, first, arrival=0.0, now=0.0) == 0
    # A burst boundary occurs after the modem tail. In the next decision the
    # challenger is already active and cheaper, but the configured dwell is
    # longer, so the established preference must be retained temporarily.
    next_burst = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="ACTIVE"),
    }
    assert call(controller, next_burst, arrival=3.0, now=3.0) == 0
    assert controller.last_decision["decision_mode"] == "session_boundary_hold"
    assert controller.persistent_switches == 0
    assert call(controller, next_burst, arrival=4.0, now=11.0) == 1
    assert controller.last_decision["decision_mode"] == "session_reoptimization"
    assert controller.persistent_switches == 1


def test_json_configuration_loads_with_explicit_runtime_overrides():
    config = load_two_timescale_config(initial_arrival_rate_pps=3.0)
    assert config.initial_arrival_rate_pps == 3.0
    assert config.minimum_dwell_s == pytest.approx(2.0)
    assert config.idle_power_w["5G NR"] == pytest.approx(0.0)


def test_invalid_candidate_context_is_rejected():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=1.0))
    candidates = {
        0: context("NB-IoT", latency=2.0, tx=0.006, setup=1.5, state="ACTIVE"),
        1: context("5G NR", latency=0.12, tx=0.00001, setup=0.5, state="ACTIVE"),
    }
    candidates[1]["reliability_pct"] = 101.0
    feasible, matrix = inputs(candidates)
    with pytest.raises(ValueError, match="reliability_pct"):
        controller.select_network_with_context(
            feasible, matrix, False, 100.0, arrival_time_s=0.0, now_s=0.0, candidates=candidates
        )
