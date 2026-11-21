# Baseline versus upgraded framework: complete implementation and evidence comparison

## 1. Reference implementation before upgrade

The reference system represents LoRaWAN-originated traffic entering a logical gateway. The gateway compares two abstract cellular backhaul candidates (NB-IoT/LTE-style and 5G NR/5GC-style), applies availability and packet-deadline feasibility, classifies four gateway states (NORMAL, EMERGENCY, LOW_BATTERY, CONFLICT), then ranks feasible candidates with design-specified AHP weights and TOPSIS. Six strategies were evaluated: fixed NB-IoT, fixed 5G, latency-first, energy-first, static equal-weight AHP-TOPSIS and adaptive state-dependent AHP-TOPSIS.

## 2. Complete six-strategy baseline comparison (A_NORMAL, 30 seeds)

| Strategy | PDR | Mean latency (s) | P95 latency (s) | Emergency PDR | Modelled energy (J/run) | Mean selector time (µs) |
|---|---:|---:|---:|---:|---:|---:|
| Fixed NB-IoT | 86.83% | 2.8689 | 7.3506 | 16.88% | 129.29 | 0.58 |
| Fixed 5G | 99.02% | 0.0274 | 0.0305 | 99.10% | 135.24 | 0.65 |
| Latency-first | 99.02% | 0.0274 | 0.0305 | 99.10% | 135.24 | 7.81 |
| Energy-first | 99.02% | 0.0274 | 0.0305 | 99.10% | 135.24 | 7.81 |
| Static equal-weight AHP-TOPSIS | 99.02% | 0.0274 | 0.0305 | 99.10% | 135.24 | 235.19 |
| Adaptive state-dependent AHP-TOPSIS | 99.02% | 0.0274 | 0.0305 | 99.10% | 135.24 | 396.98 |

**Critical baseline diagnostic:** adaptive AHP-TOPSIS selected 5G in all 5,768,175 logged primary ranking decisions. The five 5G-selecting strategies therefore have identical packet-level metrics in this operating point; their selector computation cost differs. The comparison against fixed NB-IoT is not a physical before/after deployment and does not show adaptive AHP-TOPSIS outperforming fixed 5G.

## 3. Baseline-to-upgrade implementation traceability

| Area | Before / reference | Implemented upgrade | Evidence boundary |
|---|---|---|---|
| Candidate selection | NB-IoT and 5G NR modeled as two fixed candidates. | Common profile/adapter contract; selectable NB-IoT and 5G NR adapters. | Software architecture is extensible; no 6G radio or selectable profile. |
| Decision timescale | Per-packet availability/deadline check followed by AHP-TOPSIS. | Persistent session/burst preference plus faster packet-level decision. | TSC implementation; 900 paired traces. |
| Traffic estimation | No persistent expected-burst estimate in original selector. | EWMA inter-arrival estimate and Poisson expected-cluster approximation. | Not MMPP or a learned/event classifier. |
| Energy treatment | Configured setup/transmission/CPU terms. | Currently due setup cost amortized across estimated cluster. | Idle-tail/sleep leakage and switching energy are uncalibrated/zero. |
| Emergency handling | Feasibility filter and state-dependent ranking. | Fastest-feasible packet-level override can bypass session preference. | Implemented; no significant emergency-PDR gain. |
| Outage handling | Availability/feasibility filtering in packet selection. | Forced fallback when preferred backhaul becomes unavailable/infeasible. | Tested scripted binary outages, not operator handover. |
| Switching stability | No session-level dwell/improvement guard in original path. | Configurable dwell-time and improvement threshold. | Fewer packet-selection changes not demonstrated. |
| 6G readiness | No 6G candidate interface. | IMT-2030 non-selectable profile template. | Architectural extension only; no 6G model or experiment. |

## 4. TSC multi-operating-point evaluation

The separate TSC matrix covers five offered loads (0.5, 1, 2, 4, 8 packets/s), two emergency shares (10%, 25%), three outage patterns (none, single, repeated), 30 paired seeds (1000–1029) per condition, and 120 simulated seconds per trace. Total: 30 conditions, 900 paired traces, 1,800 algorithm-run metric records, 314,332 TSC decision records and 180 paired tests.

| Metric | Adaptive AHP-TOPSIS | TSC | Descriptive difference | Inferential finding |
|---|---:|---:|---:|---|
| Pooled PDR | 93.1734% | 93.1902% | +0.0168 pp | No Holm-significant improvement in any condition |
| Mean of condition mean latency | 0.39314 s | 0.37327 s | 5.05% lower | Significant in 4/30 repeated-outage conditions at 2–4 pps |
| Mean of condition P95 latency | 2.81356 s | 2.74480 s | 2.44% lower | Significant in 3/30 repeated-outage conditions at 2–4 pps |
| Mean of condition emergency PDR | 88.4742% | 88.4593% | -0.0149 pp | No Holm-significant improvement |
| Total modelled energy over 900 traces | 9,611.767 J | 9,618.845 J | 0.0736% higher | Two conditions show small 0.31%–0.38% reductions; no overall saving |
| Mean selector computation | 269.949 µs | 42.752 µs | 84.16% lower | Significant in 30/30 conditions |
| Packet-selection changes | 2,404 | 2,436 | 32 more for TSC | No switching-reduction claim |

PDR is pooled over all generated packets. Latency/P95 and emergency PDR are unweighted means of condition-level metrics. Energy is summed across all traces. Two-sided paired Wilcoxon tests with Holm correction were applied across all 180 condition-metric comparisons.

## 5. Limitations and claim boundaries

- Logical simulation only; no physical radio, commercial modem, live operator network, full LoRaWAN PHY/MAC, complete LTE EPC/5G Core, N3IWF or standardized ATSSS.
- TSC uses EWMA inter-arrival estimation and a Poisson expected-burst approximation; it is not MMPP or learned traffic prediction.
- Configured setup/transmission energy is modelled; calibrated idle-tail/sleep leakage and switching energy are excluded/zero in the matrix. No overall energy saving is established.
- PDR and emergency-PDR gains are not statistically established; switching reductions are not demonstrated.
- IMT-2030/6G is a non-selectable architecture template only; no 6G radio/core or performance model exists.

## 6. Related-work comparison

See `REFERENCES_AND_RELATED_WORK.md` and Appendices D1–D2 in the final report for paper-by-paper methods, testbeds/evaluation, published findings, overlap and differences. The key prior-art boundaries are: LoRaWAN–5G integration (Chen 2022; Brito 2026), cellular LPWAN backhaul (Shahgholi 2021), batch/multi-RAT association (Možný 2024), AHP/fuzzy-AHP QoS-energy selection (Roy 2026; Rahayani 2026), hierarchical assignment/per-packet scheduling (Ghadimi 2026), filtered LoRa adaptation (Usman 2026) and measured modem energy (Skrastins 2026; Uitto 2026).
