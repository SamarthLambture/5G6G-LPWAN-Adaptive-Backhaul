# Contribution and Performance Impact

This document records what was present in the reference implementation, what was added, the results observed, and the limitations that constrain the claims.

## 1. Reference design

The original framework represents LoRaWAN-originated packets entering a logical edge gateway. It models two onward cellular backhaul candidates: an NB-IoT/LTE-style path and a 5G NR/5GC-style path. The gateway applies availability and packet-deadline feasibility filtering, classifies one of four operating states (NORMAL, EMERGENCY, LOW_BATTERY, CONFLICT), loads a design-specified AHP weight vector and ranks feasible candidates with TOPSIS over latency, energy, reliability and nominal bandwidth. Six strategies are compared: fixed NB-IoT, fixed 5G, latency-first, energy-first, static equal-weight AHP-TOPSIS and adaptive AHP-TOPSIS.

## 2. Added implementation

| Component | Implemented change | Boundary |
|---|---|---|
| Two-timescale controller | Session/burst-level preferred backhaul plus packet-level override/fallback | A specific controller policy; not a new general control theory. |
| Traffic estimation | EWMA inter-arrival estimator and Poisson expected-cluster estimate | No MMPP or learned regime prediction. |
| Setup-energy accounting | Amortizes currently due setup energy across estimated burst size for the session preference | No calibrated modem idle-tail/sleep or switching energy. |
| Emergency override | Fastest feasible path can temporarily override the session preference | Does not establish higher emergency PDR. |
| Availability fallback | Forced fallback when preferred path is unavailable or infeasible | Binary outage scenarios, not continuous fading/handover. |
| Switching guard | Dwell time and improvement threshold for session re-optimization | Fewer switches not demonstrated by current comparison. |
| Backhaul abstraction | Common profile/adapter interface | NB-IoT and 5G NR selectable; 6G template is non-selectable. |
| 6G profile | IMT-2030 usage-scenario/capability template | Not a 6G radio, core or performance model. |

## 3. Original primary experiment

The original dataset contains 4,320 metric rows (24 configurations × 30 seeds × 6 strategies). Fixed NB-IoT is a single-backhaul reference; fixed 5G is a control; adaptive AHP-TOPSIS is the original adaptive policy.

| Metric | Fixed NB-IoT reference | Fixed 5G | Adaptive AHP-TOPSIS |
|---|---:|---:|---:|
| PDR | 86.83% | 99.02% | 99.02% |
| Mean latency | 2.8689 s | 0.0274 s | 0.0274 s |
| P95 latency | 7.3506 s | 0.0305 s | 0.0305 s |
| Emergency PDR | 16.88% | 99.10% | 99.10% |
| Modelled total energy | 129.29 J | 135.24 J | 135.24 J |

The adaptive AHP policy selected 5G in all 5,768,175 logged primary ranking decisions. Therefore the apparent gain versus fixed NB-IoT is not a demonstrated gain over fixed 5G.

## 4. TSC 900-trace experiment

30 operating conditions = 5 offered loads × 2 emergency shares × 3 outage patterns. Each condition has 30 paired seeds. The experiment produced 900 paired input traces and 1,800 algorithm-run records at 120 simulated seconds per trace. Paired Wilcoxon tests were adjusted using Holm correction across 180 condition-metric tests.

| Finding | Result | Interpretation |
|---|---:|---|
| Selector computation | 30/30 conditions significant; 72.31%–86.48% lower | Strongest consistent result. |
| Mean latency | 4/30 conditions significant | Benefits concentrated in repeated outages at 2–4 pps. |
| P95 latency | 3/30 conditions significant | Same repeated-outage region. |
| Modelled energy | 2/30 conditions significant | Small 0.31%–0.38% reductions at 4 pps with repeated outages. |
| PDR | 0/30 conditions significant | No established improvement. |
| Emergency PDR | 0/30 conditions significant | No established improvement. |
| Packet-selection changes | 2,436 TSC vs 2,404 AHP | No switching-reduction claim. |

Across all heterogeneous conditions, pooled PDR is 93.1734% for AHP-TOPSIS and 93.1902% for TSC; mean-of-condition mean latency is 0.39314s vs 0.37327s; total modelled energy is 9,611.767J vs 9,618.845J (TSC +0.0736%). These aggregate summaries are descriptive; condition-wise inference is more appropriate.

## 5. Interpretation and limitation

TSC is best described as a lower-computation selector with latency benefits in selected repeated-outage conditions. It is not universally superior and does not establish improved delivery reliability, emergency reliability, fewer switches or overall energy saving. Energy estimates exclude calibrated modem idle-tail/sleep and switching energy. LoRaWAN PHY/MAC and full cellular protocol stacks are abstracted. The project is simulation-only. The IMT-2030 profile is a future architecture extension template, not an implemented 6G system.

## 6. Related work

See [`submission/REFERENCES_AND_RELATED_WORK.md`](./REFERENCES_AND_RELATED_WORK.md) for a representative comparison against LoRaWAN–5G integration, hybrid LPWAN backhaul, multi-RAT selection, energy-aware HetNet selection, per-packet scheduling and measured modem-energy studies. The component methods are established; the defensible contribution is their specific gateway-side coordination and evaluation.
