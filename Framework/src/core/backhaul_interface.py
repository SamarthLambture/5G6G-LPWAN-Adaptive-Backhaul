"""Technology-agnostic backhaul profile and adapter contracts.

The catalog separates *technology identity/capabilities* from runtime link
metrics. NB-IoT and 5G NR are the only profiles currently instantiated by the
SimPy model. The IMT-2030/6G entry is deliberately an exploratory template:
it has no invented latency, reliability, bandwidth or energy values and is
not eligible for normal simulation selection.

This module is an architectural extension point, not a 3GPP/ITU protocol
implementation or a claim of 6G conformance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Mapping, Protocol, runtime_checkable


class ProfileStatus(str, Enum):
    IMPLEMENTED_SIMULATED = "implemented_simulated"
    EXPLORATORY_TEMPLATE = "exploratory_template"


class CandidateValidationError(ValueError):
    """Raised when a backhaul candidate is not complete or eligible."""


REQUIRED_RUNTIME_METRICS = (
    "latency_s",
    "tx_energy_j",
    "setup_energy_j",
    "setup_energy_due_j",
    "reliability_pct",
    "bandwidth_bps",
    "tail_time_s",
)


@dataclass(frozen=True)
class BackhaulProfile:
    """Descriptive technology profile independent of a particular modem."""

    profile_id: str
    display_name: str
    radio_family: str
    generation: str
    status: ProfileStatus
    selection_enabled: bool
    capability_tags: tuple[str, ...] = ()
    design_principles: tuple[str, ...] = ()
    specification_basis: str = ""
    metric_provenance: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.profile_id or self.profile_id.strip() != self.profile_id:
            raise ValueError("profile_id must be a non-empty trimmed identifier")
        if not self.display_name:
            raise ValueError("display_name must be non-empty")
        if self.status == ProfileStatus.EXPLORATORY_TEMPLATE and self.selection_enabled:
            raise ValueError("exploratory templates cannot be enabled for normal selection")

    @property
    def is_simulation_selectable(self) -> bool:
        return self.status == ProfileStatus.IMPLEMENTED_SIMULATED and self.selection_enabled

    def describe(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "radio_family": self.radio_family,
            "generation": self.generation,
            "status": self.status.value,
            "selection_enabled": self.selection_enabled,
            "is_simulation_selectable": self.is_simulation_selectable,
            "capability_tags": list(self.capability_tags),
            "design_principles": list(self.design_principles),
            "specification_basis": self.specification_basis,
            "metric_provenance": self.metric_provenance,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RuntimeBackhaulMetrics:
    """Per-decision metrics supplied by an implemented adapter/model.

    Values are runtime model inputs. This data class does not imply that the
    values were physically measured.
    """

    latency_s: float
    tx_energy_j: float
    setup_energy_j: float
    setup_energy_due_j: float
    reliability_pct: float
    bandwidth_bps: float
    tail_time_s: float
    available: bool = True
    modem_state: str = "UNKNOWN"
    tx_time_s: float = 0.0
    provenance: str = "configured_model_estimate"

    def __post_init__(self) -> None:
        numeric = {
            "latency_s": self.latency_s,
            "tx_energy_j": self.tx_energy_j,
            "setup_energy_j": self.setup_energy_j,
            "setup_energy_due_j": self.setup_energy_due_j,
            "bandwidth_bps": self.bandwidth_bps,
            "tail_time_s": self.tail_time_s,
            "tx_time_s": self.tx_time_s,
        }
        for name, value in numeric.items():
            if not isfinite(float(value)) or float(value) < 0:
                raise CandidateValidationError(f"{name} must be finite and non-negative")
        if not isfinite(float(self.reliability_pct)) or not 0 <= float(self.reliability_pct) <= 100:
            raise CandidateValidationError("reliability_pct must be between 0 and 100")
        if self.setup_energy_due_j > self.setup_energy_j + 1e-12:
            raise CandidateValidationError("setup_energy_due_j cannot exceed setup_energy_j")
        if not self.modem_state:
            raise CandidateValidationError("modem_state must be supplied")

    def as_selection_context(self, profile: BackhaulProfile) -> dict[str, Any]:
        if not profile.is_simulation_selectable:
            raise CandidateValidationError(
                f"Profile {profile.profile_id} is not enabled for normal simulation selection"
            )
        return {
            "profile_id": profile.profile_id,
            "name": profile.display_name,
            "radio_family": profile.radio_family,
            "generation": profile.generation,
            "profile_status": profile.status.value,
            "modem_state": self.modem_state,
            "available": bool(self.available),
            "latency_s": float(self.latency_s),
            "reliability_pct": float(self.reliability_pct),
            "bandwidth_bps": float(self.bandwidth_bps),
            "tx_time_s": float(self.tx_time_s),
            "tx_energy_j": float(self.tx_energy_j),
            "setup_energy_j": float(self.setup_energy_j),
            "setup_energy_due_j": float(self.setup_energy_due_j),
            "tail_time_s": float(self.tail_time_s),
            "metric_provenance": self.provenance,
        }


@runtime_checkable
class BackhaulAdapter(Protocol):
    """Runtime contract expected from a cellular backhaul adapter."""

    profile_id: str
    rel: float
    bw: float
    avail: bool
    base_lat: float

    def estimate_delay(self, payload_bytes: int) -> float: ...
    def estimate_energy(self, payload_bytes: int) -> float: ...
    def selection_energy_context(self, payload_bytes: int, predicted_latency: float) -> Mapping[str, Any]: ...
    def add_packet(self, packet: dict[str, Any]) -> bool: ...
    def _update_q_area(self) -> None: ...
    def trigger_outage(self) -> None: ...
    def recover_outage(self) -> None: ...


class BackhaulCatalog:
    """Registry of technology profiles, with an explicit maturity boundary."""

    def __init__(self, profiles: tuple[BackhaulProfile, ...] = ()) -> None:
        self._profiles: dict[str, BackhaulProfile] = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: BackhaulProfile) -> None:
        if profile.profile_id in self._profiles:
            raise ValueError(f"Duplicate backhaul profile: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile

    def get(self, profile_id: str) -> BackhaulProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"Unknown backhaul profile: {profile_id}") from exc

    def all_profiles(self) -> tuple[BackhaulProfile, ...]:
        return tuple(self._profiles.values())

    def selectable_profiles(self) -> tuple[BackhaulProfile, ...]:
        return tuple(profile for profile in self._profiles.values() if profile.is_simulation_selectable)

    def exploratory_profiles(self) -> tuple[BackhaulProfile, ...]:
        return tuple(profile for profile in self._profiles.values() if profile.status == ProfileStatus.EXPLORATORY_TEMPLATE)

    def build_selection_context(
        self,
        profile_id: str,
        metrics: RuntimeBackhaulMetrics,
    ) -> dict[str, Any]:
        profile = self.get(profile_id)
        return metrics.as_selection_context(profile)

    def architecture_audit(self) -> dict[str, Any]:
        profiles = [profile.describe() for profile in self.all_profiles()]
        return {
            "catalog_version": "1.0",
            "profiles": profiles,
            "selectable_profile_ids": [p.profile_id for p in self.selectable_profiles()],
            "exploratory_profile_ids": [p.profile_id for p in self.exploratory_profiles()],
            "6g_radio_metrics_present": False,
            "6g_radio_metrics_status": "not supplied; IMT-2030 is represented as a capability template only",
        }


def default_backhaul_catalog() -> BackhaulCatalog:
    """Return profiles matching the current simulator scope and 6G roadmap."""
    return BackhaulCatalog((
        BackhaulProfile(
            profile_id="nb_iot",
            display_name="NB-IoT",
            radio_family="3GPP cellular LPWAN",
            generation="LTE / NB-IoT (IMT-2020-era cellular technology)",
            status=ProfileStatus.IMPLEMENTED_SIMULATED,
            selection_enabled=True,
            capability_tags=("massive_iot", "wide_area_low_power", "low_rate_telemetry"),
            specification_basis="Existing project NB-IoT-style abstracted backhaul model",
            metric_provenance="Framework/src/simulation/network.py configured simulation parameters",
            notes="Implemented as an abstracted cellular backhaul candidate; not a standards-complete modem stack.",
        ),
        BackhaulProfile(
            profile_id="5g_nr",
            display_name="5G NR",
            radio_family="3GPP cellular NR",
            generation="5G / IMT-2020",
            status=ProfileStatus.IMPLEMENTED_SIMULATED,
            selection_enabled=True,
            capability_tags=("enhanced_mobile_broadband", "massive_machine_type_communications", "urlcc_related_capabilities"),
            specification_basis="Existing project 5G-NR-style abstracted backhaul model",
            metric_provenance="Framework/src/simulation/network.py configured simulation parameters",
            notes="Implemented as an abstracted cellular backhaul candidate; not a standards-complete 5G core or radio implementation.",
        ),
        BackhaulProfile(
            profile_id="imt_2030_6g_template",
            display_name="IMT-2030 / 6G (exploratory profile)",
            radio_family="Future IMT-2030 terrestrial radio interface",
            generation="IMT-2030 (6G research direction)",
            status=ProfileStatus.EXPLORATORY_TEMPLATE,
            selection_enabled=False,
            capability_tags=(
                "immersive_communication",
                "hyper_reliable_low_latency_communication",
                "massive_communication",
                "ubiquitous_connectivity",
                "ai_and_communication",
                "integrated_sensing_and_communication",
            ),
            design_principles=("security_and_resilience", "connecting_the_unconnected", "ubiquitous_intelligence", "sustainability"),
            specification_basis=(
                "ITU-R Recommendation M.2160-0 (2023) and the IMT-2030 development process; "
                "2026 draft requirements/evaluation documents are not treated as finalized radio-interface specifications."
            ),
            metric_provenance="None: no 6G latency, energy, reliability or bandwidth values are asserted by this project.",
            notes=(
                "Architecture-only extension point. Not selectable in the current simulator; no 6G radio, core, "
                "candidate RIT/SRIT or measured performance is implemented."
            ),
        ),
    ))


DEFAULT_BACKHAUL_CATALOG = default_backhaul_catalog()


def validate_backhaul_adapters(
    adapters: tuple[BackhaulAdapter, ...] | list[BackhaulAdapter],
    catalog: BackhaulCatalog,
    *,
    required_profile_ids: tuple[str, ...] = ("nb_iot", "5g_nr"),
) -> tuple[BackhaulAdapter, ...]:
    """Validate an adapter set before it is attached to an EdgeGateway.

    The current experiment suite requires NB-IoT and 5G NR baseline profiles;
    additional selectable profiles may be appended without changing the TSC.
    """
    validated = tuple(adapters)
    if not validated:
        raise CandidateValidationError("At least one backhaul adapter must be supplied")
    seen: set[str] = set()
    methods = ("estimate_delay", "estimate_energy", "selection_energy_context", "add_packet", "_update_q_area", "trigger_outage", "recover_outage")
    runtime_attributes = ("rel", "bw", "avail")
    for adapter in validated:
        profile_id = getattr(adapter, "profile_id", None)
        if not isinstance(profile_id, str) or not profile_id:
            raise CandidateValidationError("Each adapter must expose a non-empty profile_id")
        if profile_id in seen:
            raise CandidateValidationError(f"Duplicate adapter profile_id: {profile_id}")
        seen.add(profile_id)
        profile = catalog.get(profile_id)
        if not profile.is_simulation_selectable:
            raise CandidateValidationError(f"Adapter profile {profile_id} is not selectable")
        missing = [name for name in methods if not callable(getattr(adapter, name, None))]
        if missing:
            raise CandidateValidationError(
                f"Adapter {profile_id} is missing contract methods: {', '.join(missing)}"
            )
        missing_attributes = [name for name in runtime_attributes if not hasattr(adapter, name)]
        if missing_attributes:
            raise CandidateValidationError(
                f"Adapter {profile_id} is missing runtime attributes: {', '.join(missing_attributes)}"
            )
        if profile_id == "5g_nr" and not hasattr(adapter, "base_lat"):
            raise CandidateValidationError("5g_nr adapter must expose base_lat for the existing latency-degradation event")
    missing_profiles = sorted(set(required_profile_ids) - seen)
    if missing_profiles:
        raise CandidateValidationError(
            "Adapter set is missing required baseline profiles: " + ", ".join(missing_profiles)
        )
    return validated
