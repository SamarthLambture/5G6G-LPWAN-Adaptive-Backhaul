"""Audit the generic backhaul catalog and exploratory 6G extension boundary.

The third-candidate check uses synthetic values solely to test the selector
contract. It is not a 6G model, not a simulation run, and must not be cited as
6G performance evidence.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.backhaul_interface import default_backhaul_catalog  # noqa: E402
from src.core.two_timescale import TwoTimescaleConfig, TwoTimescaleController  # noqa: E402


def synthetic_three_candidate_contract_probe() -> dict:
    controller = TwoTimescaleController(TwoTimescaleConfig(initial_arrival_rate_pps=1.0))
    candidates = {
        0: {"name": "NB-IoT", "latency_s": 0.8, "tx_energy_j": 0.04,
            "setup_energy_due_j": 0.0, "setup_energy_j": 1.5, "reliability_pct": 95.0,
            "tail_time_s": 2.0, "available": True},
        1: {"name": "5G NR", "latency_s": 0.1, "tx_energy_j": 0.03,
            "setup_energy_due_j": 0.0, "setup_energy_j": 0.5, "reliability_pct": 99.0,
            "tail_time_s": 2.0, "available": True},
        2: {"name": "Third adapter (synthetic contract fixture)", "latency_s": 0.2,
            "tx_energy_j": 0.005, "setup_energy_due_j": 0.01, "setup_energy_j": 0.1,
            "reliability_pct": 98.0, "tail_time_s": 2.0, "available": True},
    }
    matrix = np.asarray([[0.8, 0.04], [0.1, 0.03], [0.2, 0.005]], dtype=float)
    selected = controller.select_network_with_context(
        [0, 1, 2], matrix, False, 100.0,
        arrival_time_s=0.0, now_s=0.0, candidates=candidates,
    )
    return {
        "status": "passed" if selected == 2 else "failed",
        "candidate_count": len(candidates),
        "selected_index": int(selected),
        "selected_candidate_label": candidates[selected]["name"] if selected >= 0 else None,
        "fixture_type": "synthetic_interface_contract_test_only",
        "is_6g_performance_evidence": False,
        "note": "Proves the controller can process a third candidate index; values are synthetic and make no radio-performance claim.",
    }


def main() -> int:
    catalog = default_backhaul_catalog()
    audit = catalog.architecture_audit()
    probe = synthetic_three_candidate_contract_probe()
    report = {
        "title": "Technology-agnostic backhaul architecture readiness audit",
        "scope": "profile/catalog/interface validation; not a radio or end-to-end network simulation",
        "catalog": audit,
        "three_candidate_contract_probe": probe,
        "conclusions": {
            "nb_iot_and_5g_nr_profiles": "implemented_simulated",
            "imt_2030_6g_profile": "architecture_only_exploratory_template_not_selectable",
            "6g_performance_values": "not supplied; no 6G performance claims permitted",
            "controller_candidate_cardinality": "supports_more_than_two_candidate_indices at the decision-context API",
            "end_to_end_6g_adapter": "not implemented",
        },
    }
    out = ROOT / "results" / "supplementary" / "backhaul_architecture"
    out.mkdir(parents=True, exist_ok=True)
    (out / "architecture_readiness.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (out / "backhaul_profile_catalog.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "profile_id", "display_name", "radio_family", "generation", "status",
            "selection_enabled", "is_simulation_selectable", "metric_provenance", "notes",
        ])
        writer.writeheader()
        for profile in catalog.all_profiles():
            row = profile.describe()
            row["capability_tags"] = ";".join(row["capability_tags"])
            row["design_principles"] = ";".join(row["design_principles"])
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    print(json.dumps({"output": str(out), "three_candidate_probe": probe, "selectable_profiles": report["catalog"]["selectable_profile_ids"]}, indent=2))
    return 0 if probe["status"] == "passed" and "imt_2030_6g_template" in audit["exploratory_profile_ids"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
