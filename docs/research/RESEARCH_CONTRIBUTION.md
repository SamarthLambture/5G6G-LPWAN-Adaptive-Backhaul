# Final Research Contribution and Related-Work Positioning

## 1. Project identity and scope

**Project:** `5G6G-LPWAN-Adaptive-Backhaul`  
**Domain:** Computer Networks / LoRaWAN gateway cellular backhaul selection  
**Implementation:** Python/SimPy discrete-event simulation plus an interactive browser demonstration  
**Proposed extension:** Two-Timescale Adaptive Backhaul Controller (TSC)

This is not the TAVCI digital image-processing project. The project models a LoRaWAN-originated traffic stream entering a gateway, then considers a choice between two abstracted cellular backhaul candidates: NB-IoT/LTE-style and 5G NR/5GC-style. The latest architecture update adds a technology-agnostic profile/adapter contract and an IMT-2030/6G capability template that is deliberately not selectable in the simulator.

## 2. Defensible contribution statement

This work implements and evaluates a gateway-side policy that separates backhaul choice into (i) a slower session/burst preference that amortizes currently due setup energy over an estimated arrival burst and (ii) a faster packet-level decision that can override the session preference for emergency traffic or force fallback when the preferred network becomes unavailable or infeasible. The policy includes configurable dwell-time and improvement-threshold guards and records decision reasons.

The contribution is a **specific gateway-side controller integration and condition-dependent simulation evaluation** for NB-IoT versus 5G NR, now exposed through a normalized backhaul profile/adapter contract. The current 6G element is architecture extensibility only: no IMT-2030 radio profile, core, numeric performance model or measured values are implemented. It is not a new general two-timescale optimization theory, a new AHP/TOPSIS algorithm, a new wireless standard, or a first LoRaWAN–5G backhaul architecture.


## 3A. Technology-agnostic interface and 6G boundary

The latest implementation introduces `Framework/src/core/backhaul_interface.py`. It provides a normalized candidate contract, a profile registry, metric validation, and an adapter-validation function. The `EdgeGateway` builds its candidate matrix and decision context from an adapter list and accepts an optional `backhaul_adapter_factory` plus a `BackhaulCatalog`; the current experiment path preserves NB-IoT and 5G NR aliases and can append additional implemented profiles. The TSC was checked with a synthetic third candidate, confirming that its context API is not hard-coded to exactly two candidate indices.

The catalog registers `nb_iot` and `5g_nr` as implemented/simulated. `imt_2030_6g_template` is registered as `exploratory_template`, has no numeric radio metrics and is not selectable. Its capability tags follow the six IMT-2030 usage-scenario labels in ITU-R M.2160. The architecture-ready status is not a 6G radio simulation or performance result. See `UNIFIED_BACKHAUL_ARCHITECTURE.md`, `6G_EXTENSION_PROFILE.md`, and `IMPLEMENTATION_NOTE_BACKHAUL_ABSTRACTION.md`.

## 3. What prior work already establishes

| Research direction | Representative work | What it means for our claim |
|---|---|---|
| LoRaWAN–5G integration/backhaul | O. D. D. Brito, P. Pace and F. De Rango, “A Unified Backhaul Architecture for Seamless LoRaWAN IoT Integration in 5G NR Networks,” IEEE PIMRC 2026, DOI: 10.1109/PIMRC69400.2026.11711913. | LoRaWAN-to-5G integration and a unified backhaul architecture are already published. Their focus includes LoRa-frame adaptation, UDP/IP encapsulation, 5G slicing and a cognitive spectrum controller; distinguish our NB-IoT-versus-5G gateway-selection policy. |
| LoRaWAN gateway with 5G backhaul | Chen et al., “LoRaWAN-5G Integrated Network With Collaborative RAN and Converged Core Network,” IEEE PIMRC 2022, DOI: 10.1109/PIMRC54779.2022.9977480. | A 5G-based LoRaWAN gateway/backhaul testbed is established prior work. |
| Service-aware heterogeneous network selection | G. Liang and H. Yu, “Network selection algorithm for heterogeneous wireless networks based on service characteristics and user preferences,” EURASIP Journal on Wireless Communications and Networking, 2018, Article 241, DOI: 10.1186/s13638-018-1264-5. | Service-specific utility, entropy, fuzzy AHP, SAW/MEW/TOPSIS and handover reduction have already been studied. Traffic classes, MCDM or dwell/handover control alone are not novel. |
| NB-IoT lifecycle energy modelling | P. Andres-Maldonado et al., “Analytical Modeling and Experimental Validation of NB-IoT Device Energy Consumption,” IEEE Internet of Things Journal, 2019, DOI: 10.1109/JIOT.2019.2904802. | NB-IoT energy models with connection-control procedures and empirical validation on commercial devices already exist. A setup-plus-transmission-only model is incomplete. |
| NB-IoT energy in operational networks | “A First Look at Energy Consumption of NB-IoT in the Wild: Tools and Large-Scale Measurement,” IEEE/ACM Transactions on Networking, 2021. | Large-scale measurements show energy varies with coverage, long power tails and control-message repetitions. Fixed energy-per-packet assumptions can be misleading. |
| 5G UE energy versus channel conditions | M. F. Bhutta, “Experimental characterization and ML-based prediction of 5G UE energy consumption under varying channel conditions,” University of Oulu thesis, 2026. | Recent UE measurements report strong energy dependence on radio/channel conditions. This is a thesis, not a peer-reviewed journal paper, and should be labelled accordingly. |
| Energy-aware QoS/MCDM selection | Energy-aware utility/fuzzy TOPSIS and later Fuzzy-AHP/HetNet studies. | Merely combining latency, reliability, energy and adaptive weights is not a sufficient novelty claim. |

## 4. What the new multi-operating-point evidence says

A paired matrix evaluated 5 offered loads × 2 emergency fractions × 3 outage patterns × 30 seeds = 900 paired input traces (1,800 method runs) at 120 simulated seconds per trace. The matrix completed in 330.895 seconds and generated 314,332 TSC decision records.

The inferential analysis used paired two-sided Wilcoxon signed-rank tests and Holm correction across 180 metric-condition tests.

- Selector computation time was significantly lower in all 30 conditions (per-condition reductions 72.31%–86.48%).
- Mean latency was significantly lower in 4 conditions, all with repeated outages at 2 or 4 packets/s.
- P95 latency was significantly lower in 3 repeated-outage conditions at 2 or 4 packets/s.
- Modeled energy was significantly lower in 2 repeated-outage conditions at 4 packets/s, but the reductions were only 0.31%–0.38% per run.
- No PDR or emergency-PDR comparison survived Holm correction in any condition.
- All ten no-outage conditions had identical delivery, latency, P95 and modeled-energy metrics between AHP-TOPSIS and TSC.
- The one-outage conditions did not produce a statistically significant end-to-end performance advantage after correction.
- TSC did not demonstrate fewer packet-selection changes; its count was 2,436 versus 2,404 for AHP-TOPSIS across the full matrix. Outage drops were equal (64 each).
- Across all runs, the total modeled-energy sum was 0.0736% higher for TSC. The optional idle-tail and switching-energy terms were zero because no calibrated values are available.

Full raw outputs and condition-level statistics are in `Framework/results/supplementary/two_timescale/multi_operating_point/DETAILED_MATRIX_ANALYSIS.md`.

## 5. Research gap that remains plausible

The project-specific question is:

> Can a gateway separate a persistent burst-level backhaul preference from packet-level QoS overrides, so that routine traffic can amortize connection setup while urgent packets retain a feasible low-latency path, under changing availability of NB-IoT and 5G NR?

This is a focused evaluation question. The contribution is not the generic existence of two timescales, the use of EWMA/Poisson assumptions, or the use of a dwell timer. Those concepts are established. The work should be positioned around the particular gateway-side coordination policy and its observed behaviour under paired traffic/outage scenarios.

## 6. Claims to use in a paper or presentation

### Supported

- “We implement a gateway-side two-timescale backhaul policy with a session/burst preference and packet-level emergency override/fallback.”
- “The policy records explicit session, override and forced-fallback decision modes.”
- “In a 30-condition, 30-seed paired SimPy matrix, TSC used less measured selector computation time in every condition.”
- “Mean and P95 latency improvements were statistically supported only in selected repeated-outage conditions at 2–4 packets/s.”
- “The result is conditional: no PDR or emergency-PDR gain was statistically established, and overall modeled energy was slightly higher.”

### Do not claim

- “The first two-timescale cellular backhaul selector.”
- “A new AHP or TOPSIS algorithm.”
- “TSC always outperforms AHP-TOPSIS.”
- “TSC improves emergency reliability or guarantees deadlines.”
- “TSC reduces network switching.”
- “TSC saves energy overall.”
- “The model predicts real modem battery life.”
- “We implemented 6G, standards-compliant handover or a complete 5G Core.”

## 7. Highest-value next research improvements

1. **Calibrate the lifecycle energy model.** Account for connection/registration, transmit/receive, active waiting, connected/idle tail, DRX/eDRX/PSM or 5G inactive states, sleep leakage, coverage/retransmissions and switching. Do not insert arbitrary wattage values as if measured.
2. **Measure realistic 5G and NB-IoT energy under comparable conditions.** If hardware is unavailable, use a clearly parameterized literature-informed sensitivity range, and state that it is not a direct device-to-device comparison.
3. **Test fluctuating link quality, not only binary outages.** Use controlled latency/reliability profiles to test whether the dwell/improvement threshold prevents ping-pong selection. The current matrix does not establish fewer switches.
4. **Run ablations against a simple energy-feasible baseline.** Separate the effect of burst-size estimation, emergency override and switching guards. The current matrix directly compares TSC with adaptive AHP-TOPSIS.
5. **Keep all condition-wise negative findings.** Do not select only the two or four favourable operating conditions.

## 8. Selected sources

- Brito, O. D. D., Pace, P., and De Rango, F. “A Unified Backhaul Architecture for Seamless LoRaWAN IoT Integration in 5G NR Networks.” IEEE PIMRC 2026. DOI: [10.1109/PIMRC69400.2026.11711913](https://doi.org/10.1109/PIMRC69400.2026.11711913).
- Chen et al. “LoRaWAN-5G Integrated Network With Collaborative RAN and Converged Core Network.” IEEE PIMRC 2022. DOI: [10.1109/PIMRC54779.2022.9977480](https://doi.org/10.1109/PIMRC54779.2022.9977480).
- Liang, G., and Yu, H. “Network selection algorithm for heterogeneous wireless networks based on service characteristics and user preferences.” 2018. DOI: [10.1186/s13638-018-1264-5](https://doi.org/10.1186/s13638-018-1264-5).
- Andres-Maldonado, P. et al. “Analytical Modeling and Experimental Validation of NB-IoT Device Energy Consumption.” IEEE IoT Journal 2019. DOI: [10.1109/JIOT.2019.2904802](https://doi.org/10.1109/JIOT.2019.2904802).
- “A First Look at Energy Consumption of NB-IoT in the Wild: Tools and Large-Scale Measurement.” IEEE/ACM Transactions on Networking 2021. [IEEE Xplore record](https://ieeexplore.ieee.org/abstract/document/9514451).
- Bhutta, M. F. “Experimental characterization and ML-based prediction of 5G UE energy consumption under varying channel conditions.” University of Oulu thesis, 2026. [Repository record](https://oulurepo.oulu.fi/handle/10024/63555).

This is a selected related-work set, not a systematic review. No first-of-kind or priority claim is made.
