# Our Modifications and Performance Impact

## Purpose

This note explains what existed before the project, what the team implemented differently, why the simulation results changed, and what additional cost the framework introduces. It is also the source note for the **Our modifications & performance impact** page in the LPWAN Edge Intelligence application.

## 1. What existed before the project

The project uses established technologies and methods:

- LoRaWAN as an LPWAN device-access technology.
- NB-IoT as an LTE-family cellular IoT technology.
- 5G NR and 5G Core as cellular-system technologies.
- AHP and TOPSIS as established multi-criteria decision methods.
- Prior research on LPWAN/cellular integration, multi-RAT IoT, energy monitoring and RAT selection.

The project does not claim to invent these technologies or algorithms.

## 2. What the team implemented

The project-specific implementation is a five-layer logical framework with the backhaul decision at the edge gateway. Its decision pipeline:

1. Receives LoRaWAN-originated telemetry or emergency traffic at a logical gateway.
2. Estimates candidate backhaul delay and energy inputs and reads availability/reliability/bandwidth model inputs.
3. Applies a hard availability and packet-deadline feasibility filter before ranking.
4. Classifies the packet/gateway context as NORMAL, EMERGENCY, LOW_BATTERY or CONFLICT.
5. Loads one of four design-specified AHP weight vectors.
6. Uses TOPSIS to rank the feasible NB-IoT/LTE-style and 5G NR/5GC-style candidates.
7. Records delivery or a QoS drop.

The criteria are latency and energy (minimise), and configured reliability and nominal bandwidth (maximise). The pairwise comparison matrix is derived from the chosen weights using `a_ij = w_i / w_j`; its consistency is therefore by construction, not expert-survey validation.

## 3. Difference from selected 2021–2025 research

This is a representative comparison, not an exhaustive systematic review.

| Related work | Main focus | Difference in this project |
|---|---|---|
| Leenders et al. (2021), “Multi-RAT for IoT: The Potential in Combining LoRaWAN and NB-IoT” | Multi-radio capability at the IoT node, assessing energy, coverage, payload, latency, QoS and cost | The project keeps the endpoint access side as LoRaWAN and locates the backhaul decision at a logical gateway, comparing NB-IoT/LTE-style and 5G NR/5GC-style candidates. DOI: 10.1109/MCOM.008.2100382 |
| Chen et al. (2022), “LoRaWAN-5G Integrated Network With Collaborative RAN and Converged Core Network” | An integrated LoRaWAN–5G network and physical testbed | The project does not build a physical converged network; it studies gateway-side selection among two abstracted cellular backhaul paths in simulation. DOI: 10.1109/PIMRC54779.2022.9977480 |
| Chen et al. (2022), “A Survey on LPWAN-5G Integration: Main Challenges and Potential Solutions” | Survey of hybrid architecture, security, mobility, interoperability and coexistence | The project implements and evaluates one narrower gateway-side packet-selection pipeline. DOI: 10.1109/ACCESS.2022.3160193 |
| Leenders et al. (2023), “Multi-RAT IoT – What's to Gain? An Energy-Monitoring Platform” | In-field monitoring of per-packet energy, PDR and related parameters for LoRaWAN, NB-IoT and Sigfox | The project uses a configured simulation energy model and focuses on decision policy and the difference between instantaneous energy estimates and cumulative energy accounting. DOI: 10.1109/VTC2023-SPRING57618.2023.10199622 |
| Možný et al. (2024), “Characterizing Optimal LPWAN Access Delay in Massive Multi-RAT Smart Grid Deployments” | Association/load balancing of smart-grid end devices across NB-IoT and LTE-M | The project selects the cellular backhaul for LoRaWAN-originated traffic at a gateway; it does not distribute end devices between NB-IoT and LTE-M. DOI: 10.1016/j.iot.2023.101001 |
| Sadoun et al. (2025), “A Hybrid and Self-Adaptive QoS and QoE-Driven RAT Selection Strategy for IoT Devices” | Distributed deep-reinforcement-learning RAT selection with QoS/QoE and a trust factor | The project uses a centralised logical gateway decision with explicit feasibility, design-specified AHP weights and TOPSIS; it is not learning-based. DOI: 10.1016/j.adhoc.2025.103838 |

The defensible difference is the **specific decision placement, constraint-first sequence, state-dependent policy, candidate model, and evaluation design** used by this project. It is not a claim that those component techniques are individually new.

## 4. Before/reference versus after/adaptive results

**Comparison definition:** “Before” is a fixed-NB-IoT single-backhaul simulation reference, not a physical pre-deployment measurement. “After” is the implemented adaptive AHP-TOPSIS policy. Fixed 5G is retained as a control. Results are baseline means across 30 paired seeds with the same traffic scenario; this does not isolate an AHP-only causal effect.

| Metric | Fixed NB-IoT reference | Adaptive AHP-TOPSIS | Change |
|---|---:|---:|---:|
| Packet delivery ratio | 86.83% | 99.02% | +12.19 percentage points |
| Mean latency | 2.8689 s | 0.0274 s | 99.04% lower |
| P95 latency | 7.3506 s | 0.0305 s | 99.58% lower |
| Emergency PDR | 16.88% | 99.10% | +82.21 percentage points |
| Total gateway energy | 129.29 J | 135.24 J | +4.60% (+5.9466 J) |
| QoS drops per run | 606.17 | 0.00 | 606.17 fewer per run |

### Fixed-5G control

Fixed 5G and adaptive AHP-TOPSIS have identical primary baseline network metrics: 99.02% PDR, 0.0274 s mean latency, 0.0305 s P95 latency and 135.24 J total energy. The adaptive policy selected 5G in all 5,768,175 logged primary ranking decisions. The project therefore does **not** demonstrate an adaptive performance gain over fixed 5G or state-driven backhaul switching in the primary experiment.

## 5. Why the results changed

- **Hard QoS feasibility:** for a representative 200-byte emergency packet, the predicted initial-sleep latency is 2.024 s on NB-IoT and 0.120 s on 5G, against a 1 s deadline. NB-IoT is therefore removed before TOPSIS for this example; 5G remains feasible.
- **Configured candidate dominance:** for a 50-byte NORMAL telemetry packet, candidate inputs are 2.006061 s vs 0.120004 s latency, 1.506061 J vs 0.500012 J instantaneous energy estimate, 95% vs 99% configured reliability, and 66 kbps vs 100 Mbps nominal bandwidth. These model inputs favour 5G.
- **State-dependent AHP:** criterion priorities change across four design-specified states, but this did not change the selected path in the primary dataset. The primary experiment does not demonstrate state-driven switching.
- **Modem setup accounting:** in the seed-1000 diagnostic only, NB-IoT recorded 10 wake-ups and 15.0 J setup energy, while 5G recorded 141 wake-ups and 70.5 J setup energy. This explains part of the configured model's energy result; it is not a 30-seed wake-up average.

## 6. Added computational and energy cost

The mean decision execution microbenchmark is 516.425 microseconds for adaptive AHP-TOPSIS and 0.861 microseconds for the fixed-5G check, approximately 600 times higher in relative terms. The absolute measurement remains about 0.52 ms per decision in that benchmark and is distinct from simulated network packet latency.

The energy boundary accumulates CPU processing, modem setup and transmission energy. Sleep and idle-tail leakage are excluded. The instantaneous energy input used by the selector is not a forecast of full-horizon energy or future wake-up cycles.

## 7. Supplementary outage pilot (kept separate)

The five-seed supplementary outage/recovery pilot contains 30 records (5 seeds × 6 strategies) and is not merged into the 4,320-row primary matrix. The adaptive pilot reports mean PDR of 98.935%; it makes a mean of 57.2 NB-IoT selections during the 5G outage, zero 5G selections during the outage, and 3,098.2 5G selections after recovery. This is a small proof-of-behaviour for availability-driven fallback, not a physical handover test or standards-compliance demonstration.

## 8. Framework-design requirement

The project meets a **logical framework design** requirement: it defines five layers (device, gateway/access, edge management/orchestration, cellular backhaul/core, application/data), identifies the gateway as the decision point, and specifies the packet path and decision sequence. It is a simulation abstraction, not a physical deployment or standards-complete interworking topology. No full 5G Core, N3IWF, ATSSS, physical radio or 6G implementation is claimed.

## 9. Future work (not implemented)

A horizon-aware energy estimator, switching hysteresis, predictive availability, calibrated modem profiles, and larger outage experiments are proposed future work. They must not be represented as current features.
