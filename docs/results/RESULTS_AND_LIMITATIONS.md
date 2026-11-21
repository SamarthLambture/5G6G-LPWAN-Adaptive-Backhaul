# Results, limitations and claims boundary

## Evidence inventory

| Evidence set | Scope | Status |
|---|---|---|
| Primary experiment | 4,320 raw rows; 24 configurations × 30 seeds × 6 strategies | Archived historical baseline; audited, not rerun for this upgrade. |
| Original separate outage pilot | 5 seeds × 6 strategies = 30 records | Supplementary outage/recovery behaviour; not merged into primary results. |
| TSC targeted 30-seed validation | 30 paired seeds, 120 seconds each, 2 pps, 10% emergency, one 5G outage | Completed; used for initial integration validation. |
| TSC multi-operating-point matrix | 30 conditions × 30 paired seeds = 900 traces | Completed; principal comparative evidence for TSC. |
| Backhaul profile audit | NB-IoT, 5G NR, IMT-2030 profile template | Software extensibility validation; not a 6G network simulation. |

## TSC multi-operating-point results

The experiment uses identical input traces for AHP-TOPSIS and TSC within each seed/condition. Total wall-clock runtime was 330.895 seconds. The analysis performed 180 paired Wilcoxon tests and Holm-adjusted p-values across the full family of 180 comparisons.

**Descriptive totals across the 900 traces:**

- Pooled PDR: AHP-TOPSIS 93.1734%, TSC 93.1902% (+0.0168 percentage points).
- Mean of 30 condition-level emergency PDR values: AHP-TOPSIS 88.4742%, TSC 88.4593% (slightly lower for TSC).
- Mean of condition-level mean latencies: 0.39314s versus 0.37327s.
- Mean of condition-level P95 values: 2.81356s versus 2.74480s.
- Total modelled energy: 9611.767J versus 9618.845J (TSC higher by 0.0736%).
- Mean selector time: 269.949µs versus 42.752µs (TSC lower by 84.16%).

**Inferential findings after Holm correction:** decision time was lower in all 30 conditions; mean latency in 4; P95 latency in 3; modelled energy in 2; PDR and emergency PDR in zero.

## Limitations

1. **Simulation abstraction:** no physical radio, commercial modem, operator network or field deployment was tested.
2. **Protocol completeness:** detailed LoRaWAN PHY/MAC, airtime, collisions, deduplication, full LTE EPC, 5G Core, N3IWF and standardized ATSSS procedures are not implemented.
3. **Energy model:** cumulative energy includes CPU, modem setup and transmission as configured; it excludes calibrated modem idle-tail and sleep leakage. The TSC matrix sets optional idle-power and switching-energy terms to zero. The model therefore cannot support a claim of real-device energy superiority.
4. **Traffic model:** baseline traffic uses aggregate Poisson arrivals. TSC estimates inter-arrival behaviour using EWMA and a Poisson expected-burst approximation; no MMPP regime predictor or learned traffic model is implemented.
5. **Queue prediction:** current feasibility logic uses current queue/service context, but the proposed future predictive queue-risk control is not implemented.
6. **Reliability model:** the project uses configured candidate reliability and deterministic feasibility assumptions; it does not establish calibrated probabilistic deadline-miss or class-specific reliability guarantees.
7. **Switching stability:** packet-selection changes are 2,436 for TSC versus 2,404 for the AHP baseline in the matrix. A baseline persistent-controller-switch counter is not equivalent, so direct persistent-switch reduction cannot be claimed. The experiment uses binary outages rather than continuously fluctuating link-quality traces.
8. **6G boundary:** IMT-2030 is an exploratory non-selectable profile template. No 6G radio interface, core, numeric performance model or 6G performance experiment is included.
9. **Statistical coverage:** results use 30 seeds per condition and 120-second traces. Longer horizons, more channel/coverage distributions and independent replication are appropriate future work.
10. **AHP elicitation:** state weights are design-specified; the reciprocal pairwise matrix is generated from those weights, so consistency is by construction, not independent expert elicitation.
11. **Novelty scope:** the study combines established components in a specific gateway-side formulation. A focused literature review is included, but not an exhaustive systematic review or patent search.

## Claims that are supported

- A five-layer logical framework places cellular backhaul choice at a LoRaWAN gateway.
- NB-IoT and 5G NR are selectable simulated backhaul profiles through a common interface.
- AHP-TOPSIS with pre-ranking feasibility and four gateway states is implemented.
- TSC implements a session/burst preference with EWMA/Poisson burst estimation, setup-energy amortization, emergency overrides and forced fallback.
- TSC selector computation time is lower in all 30 tested operating conditions after Holm correction.
- TSC reduces mean/P95 latency in selected repeated-outage conditions at 2–4 packets/s.
- The IMT-2030 profile is an architecture-level extension point only.

## Claims that are not supported

- “We implemented 6G.”
- “The method is the first of its kind.”
- “TSC always outperforms AHP-TOPSIS.”
- “TSC improves PDR or emergency reliability.”
- “TSC reduces switching/ping-pong.”
- “TSC saves energy overall or is more energy-efficient on real hardware.”
- “The simulator implements complete LoRaWAN/3GPP interoperability.”

## Recommended next work

1. Calibrate NB-IoT and 5G modem lifecycle states with comparable device-level measurement boundaries.
2. Introduce time-varying link quality and compare TSC with AHP-TOPSIS plus simple hysteresis.
3. Compare EWMA/Poisson burst estimates with MMPP or other regime models.
4. Add predictive queue-risk constraints and quantify deadline/overflow trade-offs.
5. Conduct ablation and sensitivity studies using paired seeds and pre-registered endpoints.
