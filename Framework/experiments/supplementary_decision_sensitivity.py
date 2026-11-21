"""Controlled, synthetic TOPSIS decision sensitivity analysis.

This is NOT a new network simulation and does NOT modify primary results.
It holds latency, reliability and bandwidth assumptions fixed while scaling
only the NB-IoT per-packet energy estimate to inspect state-weight sensitivity.
The scale factor is hypothetical and is not a measured technology parameter.
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from src.core.math_engine import DynamicAHP, TOPSIS

OUT = ROOT / "results" / "supplementary"
OUT.mkdir(parents=True, exist_ok=True)

ahp = DynamicAHP()
topsis = TOPSIS()
scales = np.round(np.arange(0.01, 1.001, 0.01), 2)
payloads = (50, 200)
states = (
    ("NORMAL", False, 100.0, 10.0),
    ("LOW_BATTERY", False, 19.0, 10.0),
    ("EMERGENCY", True, 100.0, 1.0),
    ("CONFLICT", True, 19.0, 1.0),
)
rows = []

for payload in payloads:
    nb_tx_time = payload * 8 / 66000.0
    g5_tx_time = payload * 8 / 100000000.0
    nb_latency = 1.5 + 0.5 + nb_tx_time
    g5_latency = 0.1 + 0.02 + g5_tx_time
    nb_energy_base = 1.5 + 1.0 * nb_tx_time
    g5_energy = 0.5 + 3.0 * g5_tx_time

    for state, is_emerg, battery, deadline in states:
        weights, cr = ahp.calculate_weights(ahp.get_state_matrix(is_emerg, battery))
        nb_feasible = nb_latency <= deadline
        g5_feasible = g5_latency <= deadline
        for scale in scales:
            nb_energy = nb_energy_base * float(scale)
            dm = np.array([
                [nb_latency, nb_energy, 0.95, 66000.0],
                [g5_latency, g5_energy, 0.99, 100000000.0],
            ], dtype=float)
            feasible = []
            if nb_feasible:
                feasible.append(0)
            if g5_feasible:
                feasible.append(1)
            if len(feasible) == 0:
                selected = "NONE"
            elif len(feasible) == 1:
                selected = "NB" if feasible[0] == 0 else "5G"
            else:
                local_idx = topsis.rank_alternatives(
                    dm[feasible], weights, [-1, -1, 1, 1],
                    ["latency", "energy", "reliability", "bandwidth"]
                )
                selected = "NB" if feasible[local_idx] == 0 else "5G"
            rows.append({
                "Payload_Bytes": payload,
                "State": state,
                "NB_Energy_Scale": float(scale),
                "NB_Estimated_Energy_J": nb_energy,
                "5G_Estimated_Energy_J": g5_energy,
                "NB_Predicted_Latency_s": nb_latency,
                "5G_Predicted_Latency_s": g5_latency,
                "NB_Feasible": nb_feasible,
                "5G_Feasible": g5_feasible,
                "Selected_Backhaul": selected,
                "AHP_CR": cr,
                "Nature": "Synthetic decision sensitivity; not a network simulation",
            })

csv_path = OUT / "decision_sensitivity.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# Summarize first scale at which NB is selected for each state/payload.
summary = []
for payload in payloads:
    for state, *_ in states:
        subset = [r for r in rows if r["Payload_Bytes"] == payload and r["State"] == state]
        nb_scales = [r["NB_Energy_Scale"] for r in subset if r["Selected_Backhaul"] == "NB"]
        summary.append({
            "Payload_Bytes": payload,
            "State": state,
            "Highest_NB_Selecting_Scale": max(nb_scales) if nb_scales else "Not selected in tested range",
            "NB_Selection_Count": len(nb_scales),
            "Tested_Scales": len(subset),
            "Interpretation": "Hypothetical energy-estimate perturbation; not a calibrated physical scenario",
        })
summary_path = OUT / "decision_sensitivity_summary.csv"
with summary_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
    writer.writeheader()
    writer.writerows(summary)

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, payload in zip(axes, payloads):
    for state, *_ in states:
        subset = [r for r in rows if r["Payload_Bytes"] == payload and r["State"] == state]
        # 1 means NB; 0 means 5G. This is a decision map, not performance data.
        y = [1 if r["Selected_Backhaul"] == "NB" else 0 for r in subset]
        ax.step([r["NB_Energy_Scale"] for r in subset], y, where="post", label=state)
    ax.set_title(f"Payload = {payload} bytes")
    ax.set_xlabel("Hypothetical NB-IoT energy-estimate scale")
    ax.set_xlim(0.01, 1.0)
    ax.set_ylim(-0.1, 1.1)
    ax.set_yticks([0, 1], labels=["5G", "NB-IoT"])
    ax.grid(True, alpha=0.3)
axes[0].set_ylabel("TOPSIS selection")
axes[1].legend(title="AHP state", loc="best")
fig.suptitle("Supplementary synthetic decision sensitivity (not simulated network performance)")
fig.tight_layout()
fig.savefig(OUT / "decision_sensitivity.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print(f"Wrote {csv_path}")
print(f"Wrote {summary_path}")
print(f"Wrote {OUT / 'decision_sensitivity.png'}")
print("Rows:", len(rows))
print("Summary:")
for r in summary:
    print(r)
