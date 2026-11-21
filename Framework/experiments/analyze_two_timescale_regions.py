"""Analytical operating-region analysis for the two-timescale controller.

This script does NOT run SimPy and does NOT modify primary experiment data.
It uses the existing simulator's configured link parameters and setup/tx energy
model. Idle-tail power is omitted because the original simulator has no such
parameter; the break-even table quantifies the extra idle energy that would be
needed to change a decision, without inventing a measured idle-power value.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "results" / "supplementary" / "two_timescale"
OUT.mkdir(parents=True, exist_ok=True)

LINKS = {
    "NB-IoT": {"bw_bps": 66_000.0, "base_latency_s": 0.5, "setup_delay_s": 1.5,
               "setup_energy_j": 1.5, "tx_power_w": 1.0, "reliability_pct": 95.0},
    "5G NR": {"bw_bps": 100_000_000.0, "base_latency_s": 0.02, "setup_delay_s": 0.1,
              "setup_energy_j": 0.5, "tx_power_w": 3.0, "reliability_pct": 99.0},
}
TAIL_TIME_S = 2.0
MAX_EXPECTED_PACKETS = 10_000.0
RATES_PPS = [0.5, 1.0, 1.5, 2.0, 2.25, 2.5, 3.0, 4.0, 8.0]
MODEM_STATES = [
    ("NB_ACTIVE_5G_SLEEP", "ACTIVE", "SLEEP"),
    ("NB_SLEEP_5G_ACTIVE", "SLEEP", "ACTIVE"),
    ("BOTH_SLEEP", "SLEEP", "SLEEP"),
    ("BOTH_ACTIVE", "ACTIVE", "ACTIVE"),
]
TRAFFIC = [
    ("Telemetry_50B", 50, 10.0),
    ("Emergency_200B", 200, 1.0),
]


def expected_cluster_size(rate_pps: float, tail_s: float) -> float:
    return min(MAX_EXPECTED_PACKETS, max(1.0, math.exp(min(rate_pps * tail_s, math.log(MAX_EXPECTED_PACKETS)))))


def tx_energy(link: dict, payload_bytes: int) -> float:
    return link["tx_power_w"] * (payload_bytes * 8.0 / link["bw_bps"])


def latency(link: dict, payload_bytes: int, modem_state: str) -> float:
    setup_delay = link["setup_delay_s"] if modem_state == "SLEEP" else 0.0
    return setup_delay + link["base_latency_s"] + payload_bytes * 8.0 / link["bw_bps"]


def session_energy_per_packet(link: dict, payload_bytes: int, modem_state: str, n_packets: float) -> float:
    setup_due = link["setup_energy_j"] if modem_state == "SLEEP" else 0.0
    return setup_due / n_packets + tx_energy(link, payload_bytes)


rows = []
break_even_rows = []
for traffic_name, payload, deadline in TRAFFIC:
    for rate in RATES_PPS:
        n_packets = expected_cluster_size(rate, TAIL_TIME_S)
        for state_name, nb_state, g5_state in MODEM_STATES:
            nb_latency = latency(LINKS["NB-IoT"], payload, nb_state)
            g5_latency = latency(LINKS["5G NR"], payload, g5_state)
            nb_feasible = nb_latency <= deadline
            g5_feasible = g5_latency <= deadline
            nb_cost = session_energy_per_packet(LINKS["NB-IoT"], payload, nb_state, n_packets)
            g5_cost = session_energy_per_packet(LINKS["5G NR"], payload, g5_state, n_packets)
            if nb_feasible and g5_feasible:
                if traffic_name == "Emergency_200B":
                    selected = "NB-IoT" if nb_latency < g5_latency else "5G NR"
                else:
                    selected = "NB-IoT" if nb_cost < g5_cost else "5G NR"
            elif nb_feasible:
                selected = "NB-IoT"
            elif g5_feasible:
                selected = "5G NR"
            else:
                selected = "NONE"
            rows.append({
                "Traffic_Class": traffic_name,
                "Payload_Bytes": payload,
                "Deadline_s": deadline,
                "Offered_Load_pps": rate,
                "Modem_State_Combination": state_name,
                "NB_Modem_State": nb_state,
                "5G_Modem_State": g5_state,
                "Tail_Timer_s": TAIL_TIME_S,
                "Expected_Packets_Per_Poisson_Burst": n_packets,
                "NB_Predicted_Latency_s": nb_latency,
                "5G_Predicted_Latency_s": g5_latency,
                "NB_Feasible": nb_feasible,
                "5G_Feasible": g5_feasible,
                "NB_Session_Energy_J_Per_Packet": nb_cost,
                "5G_Session_Energy_J_Per_Packet": g5_cost,
                "Selected_Backhaul": selected,
                "Evaluation_Type": "Analytical model-based operating-region analysis; not packet simulation",
                "Idle_Tail_Power_Included": False,
            })
            # How much additional 5G idle energy per session would make NB's
            # session total cheaper? This is a threshold, not an assumed value.
            required_extra_5g_idle_j = max(0.0, (nb_cost - g5_cost) * n_packets)
            break_even_rows.append({
                "Traffic_Class": traffic_name,
                "Offered_Load_pps": rate,
                "Modem_State_Combination": state_name,
                "Expected_Packets_Per_Burst": n_packets,
                "NB_Base_Energy_J_Per_Packet": nb_cost,
                "5G_Base_Energy_J_Per_Packet": g5_cost,
                "Additional_5G_Idle_Energy_Required_For_NB_To_Be_Cheaper_J_Per_Session": required_extra_5g_idle_j,
                "Equivalent_Differential_5G_Idle_Power_Over_2s_W": required_extra_5g_idle_j / TAIL_TIME_S,
                "Interpretation": "Break-even threshold only; not a measured or assumed modem idle-power value",
            })

regions = pd.DataFrame(rows)
break_even = pd.DataFrame(break_even_rows)
regions.to_csv(OUT / "operating_regions.csv", index=False)
break_even.to_csv(OUT / "break_even_idle_energy.csv", index=False)

# Compact decision-region chart for routine 50-byte telemetry.
telemetry = regions[regions["Traffic_Class"] == "Telemetry_50B"].copy()
pivot = telemetry.pivot(index="Modem_State_Combination", columns="Offered_Load_pps", values="Selected_Backhaul")
code = {"NONE": 0, "NB-IoT": 1, "5G NR": 2}
image = pivot.apply(lambda col: col.map(code)).astype(float)
fig, ax = plt.subplots(figsize=(11, 4.6))
im = ax.imshow(image.values, aspect="auto", interpolation="nearest", vmin=0, vmax=2, cmap="viridis")
ax.set_xticks(range(len(image.columns)), [str(x) for x in image.columns])
ax.set_yticks(range(len(image.index)), image.index)
ax.set_xlabel("Offered load (packets/s); Poisson cluster estimate uses 2 s tail timer")
ax.set_title("Analytical backhaul decision regions — 50-byte telemetry")
for yi, row in enumerate(image.values):
    for xi, val in enumerate(row):
        label = {0: "None", 1: "NB", 2: "5G"}.get(int(val), "")
        ax.text(xi, yi, label, ha="center", va="center", color="white", fontsize=8)
fig.colorbar(im, ax=ax, ticks=[0, 1, 2], label="Selected candidate (0=None, 1=NB-IoT, 2=5G NR)")
fig.tight_layout()
fig.savefig(OUT / "decision_regions.png", dpi=180)
plt.close(fig)

metadata = {
    "analysis": "Two-timescale controller analytical operating regions",
    "generated_by": "Framework/experiments/analyze_two_timescale_regions.py",
    "simulation_executed": False,
    "historical_results_modified": False,
    "link_parameters_source": "Existing BackhaulModem defaults in Framework/src/simulation/network.py",
    "tail_timer_s": TAIL_TIME_S,
    "expected_poisson_burst_size": "min(10000, exp(lambda_pps * tail_timer_s))",
    "energy_model": "setup energy due now amortized over expected burst size + per-packet transmit energy",
    "idle_tail_power": "Excluded because the original model does not define it; break_even_idle_energy.csv reports required thresholds only.",
    "limitations": [
        "Analytical operating-region analysis, not discrete-event network simulation.",
        "Assumes Poisson arrivals and a fixed modem tail timer.",
        "Uses model setup and transmit parameters, not hardware measurements.",
        "Does not include modem idle-tail power, switching energy, queue contention, or stochastic reliability outcomes.",
        "The controller's runtime arrival-rate EWMA will differ from the fixed offered-load values used for this sweep."
    ],
    "rows": len(regions),
}
(OUT / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(f"Wrote {len(regions)} analytical rows to {OUT}")
print("No SimPy simulation was run; historical result files were not modified.")
print("Telemetry selections:")
print(telemetry.groupby(["Modem_State_Combination", "Selected_Backhaul"], as_index=False).size().to_string(index=False))
