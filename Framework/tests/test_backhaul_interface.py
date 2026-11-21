"""Tests for the technology-agnostic backhaul profile contract."""
import numpy as np
import pytest

from src.core.backhaul_interface import (
    BackhaulCatalog,
    BackhaulProfile,
    CandidateValidationError,
    ProfileStatus,
    RuntimeBackhaulMetrics,
    default_backhaul_catalog,
    validate_backhaul_adapters,
)
from src.core.two_timescale import TwoTimescaleConfig, TwoTimescaleController


def valid_metrics(**overrides):
    values = dict(
        latency_s=0.15,
        tx_energy_j=0.02,
        setup_energy_j=0.5,
        setup_energy_due_j=0.0,
        reliability_pct=99.0,
        bandwidth_bps=10_000_000.0,
        tail_time_s=2.0,
        available=True,
        modem_state="ACTIVE",
        tx_time_s=0.001,
        provenance="unit_test_fixture_only",
    )
    values.update(overrides)
    return RuntimeBackhaulMetrics(**values)


def test_default_catalog_has_two_implemented_profiles_and_one_6g_template():
    catalog = default_backhaul_catalog()
    assert {p.profile_id for p in catalog.selectable_profiles()} == {"nb_iot", "5g_nr"}
    exploratory = catalog.exploratory_profiles()
    assert len(exploratory) == 1
    assert exploratory[0].profile_id == "imt_2030_6g_template"
    assert exploratory[0].selection_enabled is False
    assert catalog.get("imt_2030_6g_template").is_simulation_selectable is False


def test_6g_profile_has_itu_imt2030_capability_tags_without_invented_radio_metrics():
    profile = default_backhaul_catalog().get("imt_2030_6g_template")
    assert {
        "immersive_communication",
        "hyper_reliable_low_latency_communication",
        "massive_communication",
        "ubiquitous_connectivity",
        "ai_and_communication",
        "integrated_sensing_and_communication",
    }.issubset(set(profile.capability_tags))
    assert "None" in profile.metric_provenance
    assert "no 6g radio" in profile.notes.lower() and "not selectable" in profile.notes.lower()


def test_exploratory_profile_cannot_be_registered_as_normal_selectable():
    with pytest.raises(ValueError, match="exploratory templates"):
        BackhaulProfile(
            profile_id="invalid_6g",
            display_name="Invalid 6G selectable",
            radio_family="future",
            generation="IMT-2030",
            status=ProfileStatus.EXPLORATORY_TEMPLATE,
            selection_enabled=True,
        )


def test_candidate_context_uses_profile_identity_and_metric_provenance():
    catalog = default_backhaul_catalog()
    context = catalog.build_selection_context("5g_nr", valid_metrics())
    assert context["profile_id"] == "5g_nr"
    assert context["name"] == "5G NR"
    assert context["profile_status"] == "implemented_simulated"
    assert context["metric_provenance"] == "unit_test_fixture_only"


def test_6g_template_cannot_become_simulation_candidate_without_profile_promotion():
    catalog = default_backhaul_catalog()
    with pytest.raises(CandidateValidationError, match="not enabled"):
        catalog.build_selection_context("imt_2030_6g_template", valid_metrics())


def test_runtime_metrics_reject_invalid_or_incomplete_physical_values():
    with pytest.raises(CandidateValidationError, match="latency_s"):
        valid_metrics(latency_s=-0.1)
    with pytest.raises(CandidateValidationError, match="reliability_pct"):
        valid_metrics(reliability_pct=101.0)
    with pytest.raises(CandidateValidationError, match="setup_energy_due_j"):
        valid_metrics(setup_energy_j=0.1, setup_energy_due_j=0.2)


def test_catalog_audit_explicitly_reports_6g_metrics_unavailable():
    audit = default_backhaul_catalog().architecture_audit()
    assert audit["selectable_profile_ids"] == ["nb_iot", "5g_nr"]
    assert audit["exploratory_profile_ids"] == ["imt_2030_6g_template"]
    assert audit["6g_radio_metrics_present"] is False


def test_tsc_accepts_a_third_candidate_without_assuming_two_networks():
    """Synthetic contract test only; not a 6G performance result."""
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=1.0))
    candidates = {
        0: {
            "profile_id": "nb_iot", "name": "NB-IoT", "latency_s": 0.8, "tx_energy_j": 0.04,
            "setup_energy_due_j": 0.0, "setup_energy_j": 1.5,
            "reliability_pct": 95.0, "tail_time_s": 2.0,
            "available": True,
        },
        1: {
            "profile_id": "5g_nr", "name": "5G NR", "latency_s": 0.1, "tx_energy_j": 0.03,
            "setup_energy_due_j": 0.0, "setup_energy_j": 0.5,
            "reliability_pct": 99.0, "tail_time_s": 2.0,
            "available": True,
        },
        2: {
            "profile_id": "research_rat_x", "name": "Third adapter (synthetic contract fixture)",
            "latency_s": 0.2, "tx_energy_j": 0.005,
            "setup_energy_due_j": 0.01, "setup_energy_j": 0.1,
            "reliability_pct": 98.0, "tail_time_s": 2.0,
            "available": True,
        },
    }
    matrix = np.array([[0.8, 0.04], [0.1, 0.03], [0.2, 0.005]], dtype=float)
    selected = controller.select_network_with_context(
        [0, 1, 2], matrix, False, 100.0,
        arrival_time_s=0.0, now_s=0.0, candidates=candidates,
    )
    assert selected == 2
    assert controller.last_decision["selected_profile_id"] == "research_rat_x"
    assert controller.last_decision["candidate_profile_ids"]["0"] == "nb_iot"
    assert controller.last_decision["candidate_costs_j_per_packet"]["2"] < controller.last_decision["candidate_costs_j_per_packet"]["0"]


class _ContractAdapter:
    def __init__(self, profile_id):
        self.profile_id = profile_id
        self.rel = 99.0
        self.bw = 1_000_000.0
        self.avail = True
        self.base_lat = 0.1

    def estimate_delay(self, payload_bytes):
        return 0.1

    def estimate_energy(self, payload_bytes):
        return 0.01

    def selection_energy_context(self, payload_bytes, predicted_latency):
        return {}

    def add_packet(self, packet):
        return True

    def _update_q_area(self):
        return None

    def trigger_outage(self):
        return None

    def recover_outage(self):
        return None


def test_adapter_contract_allows_an_additional_implemented_profile():
    catalog = default_backhaul_catalog()
    catalog.register(BackhaulProfile(
        profile_id="research_rat_x",
        display_name="Research RAT X",
        radio_family="custom cellular adapter",
        generation="research profile",
        status=ProfileStatus.IMPLEMENTED_SIMULATED,
        selection_enabled=True,
        metric_provenance="custom simulator module",
    ))
    adapters = (
        _ContractAdapter("nb_iot"),
        _ContractAdapter("5g_nr"),
        _ContractAdapter("research_rat_x"),
    )
    validated = validate_backhaul_adapters(adapters, catalog)
    assert len(validated) == 3
    assert [adapter.profile_id for adapter in validated][-1] == "research_rat_x"


def test_adapter_contract_rejects_exploratory_6g_profile():
    catalog = default_backhaul_catalog()
    adapters = (
        _ContractAdapter("nb_iot"),
        _ContractAdapter("5g_nr"),
        _ContractAdapter("imt_2030_6g_template"),
    )
    with pytest.raises(CandidateValidationError, match="not selectable"):
        validate_backhaul_adapters(adapters, catalog)


def test_adapter_contract_rejects_duplicate_ids_and_missing_methods():
    catalog = default_backhaul_catalog()
    with pytest.raises(CandidateValidationError, match="Duplicate"):
        validate_backhaul_adapters((_ContractAdapter("nb_iot"), _ContractAdapter("nb_iot")), catalog)

    class IncompleteAdapter:
        profile_id = "nb_iot"
        def estimate_delay(self, payload_bytes):
            return 0.1

    with pytest.raises(CandidateValidationError, match="missing contract methods"):
        validate_backhaul_adapters((IncompleteAdapter(), _ContractAdapter("5g_nr")), catalog)


def test_tsc_rejects_candidate_index_without_matrix_row():
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=1.0))
    candidates = {
        0: {"name": "NB-IoT", "latency_s": 0.8, "tx_energy_j": 0.04,
            "setup_energy_due_j": 0.0, "setup_energy_j": 1.5,
            "reliability_pct": 95.0, "tail_time_s": 2.0, "available": True},
        2: {"name": "Third adapter", "latency_s": 0.2, "tx_energy_j": 0.005,
            "setup_energy_due_j": 0.01, "setup_energy_j": 0.1,
            "reliability_pct": 98.0, "tail_time_s": 2.0, "available": True},
    }
    with pytest.raises(ValueError, match="row for every feasible candidate"):
        controller.select_network_with_context(
            [0, 2], np.array([[0.8, 0.04], [0.2, 0.005]], dtype=float), False, 100.0,
            arrival_time_s=0.0, now_s=0.0, candidates=candidates,
        )
