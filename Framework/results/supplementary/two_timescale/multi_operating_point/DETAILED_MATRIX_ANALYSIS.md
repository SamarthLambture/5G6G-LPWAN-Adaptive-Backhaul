# Multi-Operating-Point Evaluation — Two-Timescale Controller

## Executive result

The completed paired matrix evaluates the Two-Timescale Controller (TSC) against the existing adaptive AHP-TOPSIS selector across **30 operating conditions and 900 paired traces**. The evidence is mixed and condition-dependent. TSC has a consistently faster measured selector path, and it improves mean/P95 latency in a small subset of repeated-outage conditions. It does **not** demonstrate a statistically significant PDR or emergency-PDR improvement across any condition. Total modeled energy is slightly higher when all 900 runs are descriptively aggregated, although small energy reductions are statistically significant in two 4-packet/s repeated-outage conditions.

The strongest defensible conclusion is therefore: **TSC is a lower-computation gateway policy with latency benefits under selected repeated-outage, moderate/high-load conditions in this simulator. It is not universally better, does not establish an emergency-reliability gain, and does not establish an overall energy-saving advantage.**

## Experiment design and provenance

| Item | Value |
|---|---:|
| Offered load | 0.5, 1, 2, 4, 8 packets/s |
| Emergency fraction | 10%, 25% |
| Outage pattern | none, single 5G outage, repeated 5G outages |
| Single outage | 40–60 s |
| Repeated outages | 3 non-overlapping outages at 20%, 45%, 70% of 120 s; each 10 s |
| Simulated duration per trace | 120 s |
| Seeds per condition | 30 (1000–1029) |
| Operating conditions | 30 |
| Paired traces | 900 |
| Method-run metric rows | 1,800 |
| TSC decision records | 314,332 |
| Hypothesis tests | 180 (6 metrics × 30 conditions) |
| Wall-clock runtime | 330.895 s |
| Input pairing | Same generated trace for AHP-TOPSIS and TSC within each seed/condition |
| Historical results modified | No |

The analysis uses paired differences per seed within each operating condition. Two-sided Wilcoxon signed-rank tests are applied, with Holm adjustment across all 180 metric-condition tests. The reported 95% confidence intervals are t-based intervals for the **mean paired difference** and are not multiplicity-adjusted. The p-value correction is across all 180 tests.

## Descriptive summary across the full matrix

These totals and averages span deliberately different loads and outage conditions. They are descriptive summaries of the full experiment matrix, **not one homogeneous production operating point** and not a substitute for the condition-wise paired tests.

| Metric | AHP-TOPSIS | TSC | Descriptive difference |
|---|---:|---:|---:|
| Generated packets | 332,478 | 332,478 | Identical input volume |
| Delivered packets | 309,781 | 309,837 | +56 |
| Pooled PDR | 93.1734% | 93.1902% | +0.0168 percentage points |
| Pooled emergency PDR | 86.4797% | 86.4744% | -0.0052 percentage points |
| Mean of run-level mean latencies | 0.39314 s | 0.37327 s | -5.05% |
| Mean of run-level P95 latencies | 2.81356 s | 2.74480 s | -2.44% |
| Sum of modeled energy over all runs | 9611.767 J | 9618.845 J | +0.0736% |
| Mean selector computation time | 269.949 µs | 42.752 µs | -84.16% |

The pooled PDR differs by only +0.0168 percentage points, and pooled emergency PDR is marginally lower for TSC. Neither metric has a condition-level statistically significant result after Holm correction.

## Condition-wise inferential findings

Out of 180 tests, the following remained significant after Holm correction at 0.05:

| Metric | Significant conditions |
|---|---:|
| Mean decision computation time | 30/30 |
| Mean latency | 4/30 |
| P95 latency | 3/30 |
| Total modeled energy | 2/30 |
| PDR | 0/30 |
| Emergency PDR | 0/30 |

### Significant end-to-end metric results

All rows below are repeated-outage conditions. Confidence intervals are for the mean paired difference (TSC − AHP-TOPSIS); negative values favour TSC for the listed latency and energy metrics.

| Metric | Load (pps) | Emergency share | Outage | AHP mean | TSC mean | Relative change | 95% CI of paired difference | Holm p | Better / tied / worse seeds |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Mean latency | 2 | 10% | repeated | 0.7804 | 0.5651 | -27.58% | [-0.2923, -0.1382] | 0.002623 | 24/6/0 |
| Mean latency | 2 | 25% | repeated | 0.4443 | 0.4033 | -9.23% | [-0.0679, -0.0141] | 0.02789 | 18/12/0 |
| Mean latency | 4 | 10% | repeated | 1.3903 | 1.2533 | -9.85% | [-0.1734, -0.1005] | 0.0003837 | 29/1/0 |
| Mean latency | 4 | 25% | repeated | 1.0373 | 0.9361 | -9.75% | [-0.1358, -0.0665] | 0.0003837 | 29/1/0 |
| P95 latency | 2 | 10% | repeated | 3.4116 | 2.8870 | -15.38% | [-0.7485, -0.3006] | 0.003863 | 23/7/0 |
| P95 latency | 4 | 10% | repeated | 8.1414 | 7.6525 | -6.01% | [-0.6490, -0.3288] | 0.0003837 | 29/1/0 |
| P95 latency | 4 | 25% | repeated | 6.3374 | 5.9160 | -6.65% | [-0.5595, -0.2832] | 0.0005533 | 28/2/0 |
| Modeled energy | 4 | 10% | repeated | 11.9680 | 11.9230 | -0.38% | [-0.0569, -0.0330] | 0.0003837 | 29/1/0 |
| Modeled energy | 4 | 25% | repeated | 11.8903 | 11.8536 | -0.31% | [-0.0489, -0.0245] | 0.0003824 | 29/1/0 |

At 2 packets/s and 10% emergency traffic with repeated outages, TSC lowered mean latency by 27.58% and P95 latency by 15.38%, but its modeled energy was 2.04% higher (not significant). At 2 packets/s and 25% emergency traffic with repeated outages, the mean latency reduction was 9.23%; the P95 reduction did not survive Holm correction, and energy was 0.41% higher (not significant).

At 4 packets/s under repeated outages, mean latency was about 9.8% lower, P95 was 6.0–6.7% lower, and modeled energy was 0.31–0.38% lower. The energy effect is statistically detectable in this model but is small in magnitude and must not be interpreted as a real-device energy advantage.

### Selector computation time

TSC's measured mean selector computation time was lower in **all 30 conditions**, with per-condition reductions ranging from **72.31% to 86.48%** (mean reduction 84.05%). This compares the two Python selector implementations in the same experiment environment. It is not radio latency, network delay or a hardware-independent complexity guarantee.

## What the operating patterns show

### No outage

Across all ten no-outage conditions, the packet-delivery, latency, P95 latency and modeled-energy outputs were identical between AHP-TOPSIS and TSC. The gateway selected 5G for all recorded packet selections in this stable configuration. TSC still used less selector computation time. This is evidence that the new policy does not improve end-to-end behaviour when the baseline already makes the same feasible selections.

### One outage

Across the ten single-outage conditions, no PDR, emergency-PDR, latency, P95-latency or energy comparison survived the global Holm correction. The policy performs forced fallback and recovery, but a performance advantage over AHP-TOPSIS is not established in this matrix.

### Repeated outages

The significant latency and energy differences are concentrated in repeated outages at 2 and 4 packets/s. At 8 packets/s, the matrix does not show a statistically significant end-to-end advantage. This suggests the policy's benefit depends on the combination of outage recurrence and traffic load rather than being universal.

## Controller behaviour recorded

The TSC decision log contains 314,332 entries:

| Decision mode | Count | Share |
|---|---:|---:|
| `session_hold` | 254,621 | 81.00% |
| `emergency_fastest_feasible` | 49,354 | 15.70% |
| `session_start` | 7,301 | 2.32% |
| `forced_feasibility_fallback` | 1,417 | 0.45% |
| `session_reoptimization` | 999 | 0.32% |
| `packet_qos_override` | 640 | 0.20% |

Across the matrix, the TSC counters record 2,416 persistent controller switches, 640 packet-level QoS overrides and 1,417 forced fallbacks. The baseline's `Persistent_Controller_Switches` field is not an equivalent measured counter, so a direct comparison of that column is invalid. A separate packet-selection-change counter records 2,404 baseline selection changes versus 2,436 TSC selection changes; TSC does not demonstrate a reduction in that count. Outage drops are 64 for AHP-TOPSIS and 64 for TSC.

## Interpretation boundaries and limitations

1. This is a Python/SimPy simulation under the project's configured abstractions, not a physical modem or field deployment.
2. Idle-tail power and sleep leakage are excluded because calibrated values are unavailable. The TSC matrix sets optional idle power and switching energy to zero.
3. The energy reductions observed in two repeated-outage conditions are small and model-dependent. The full-matrix modeled-energy sum is +0.0736% for TSC, i.e. slightly higher overall.
4. No statistically significant PDR or emergency-PDR improvement was demonstrated in any operating condition.
5. The matrix tests binary outages, not continuous fluctuating link quality or ping-pong handover conditions. It does not establish fewer switches.
6. The 5G and NB-IoT backhauls are abstracted candidates; the work does not implement 3GPP-standardized handover, a complete 5G Core or 6G.
7. The 30-seed matrix uses 120-second traces. Longer-duration and broader channel/coverage distributions remain future work.
8. The decision-time result is an implementation benchmark in this runtime, not a universal latency or algorithmic complexity claim.

## Research conclusion

The matrix supports a **conditional** contribution: a two-timescale gateway policy that has much lower selector computation time in every tested condition and reduces latency in selected repeated-outage, 2–4 packet/s conditions. It does not support universal superiority, a PDR gain, an emergency reliability gain, fewer switches or a general energy saving. These negative findings should be included in the report and discussed in a professor presentation; they make the evaluation more credible.

## Files and reproduction

Raw inputs, decision records, summaries, statistics, run metadata and plots are stored in this directory. Reproduce on a Python environment with the project dependencies installed:

```powershell
cd Framework
py -3.13 experiments/run_two_timescale_matrix.py --duration-s 120 --rates-pps 0.5,1,2,4,8 --emergency-ratios 0.10,0.25 --outage-patterns none,single,repeated --seeds 1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029 --max-runtime-s 900
py -3.13 experiments/analyze_two_timescale_matrix.py
```

The uploaded result archive contains the completed outputs from the user's execution. Re-running the experiment is not required to inspect the supplied data.
