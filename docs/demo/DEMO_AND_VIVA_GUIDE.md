# Professor demonstration and viva guide

## 60-second project explanation

We study gateway-side cellular backhaul selection for LoRaWAN-originated IoT traffic. The original framework checks candidate availability and packet deadline feasibility, identifies one of four gateway states, and ranks feasible NB-IoT and 5G NR backhaul abstractions using state-dependent AHP weights and TOPSIS. We added a two-timescale controller: a slower session/burst preference and a faster packet-level QoS decision that can override the preference for emergency traffic or force fallback during unavailability. A technology-agnostic backhaul profile interface allows additional candidate adapters; an IMT-2030/6G profile is included only as a non-selectable template. We evaluated TSC over 30 operating conditions and 900 paired traces. Selector computation time was lower in every condition, and latency improved in selected repeated-outage conditions. We did not establish better PDR, emergency reliability, fewer switches or overall energy savings.

## What existed vs what we changed

| Before/reference | Added/changed | Why it matters |
|---|---|---|
| Packet-level AHP-TOPSIS decision | Session/burst preference with packet-level override | Separates slower modem/session decisions from urgent packet requirements. |
| Hard availability/deadline feasibility | Kept as a mandatory gate | Prevents ranking an unavailable or deadline-infeasible candidate. |
| Two hard-coded backhaul types | Profile/adapter contract | Makes the decision layer less coupled to two candidate indices. |
| NB-IoT and 5G NR only | Non-selectable IMT-2030 profile template | Shows extension point without inventing 6G measurements. |
| 4,320-row baseline | Separate 900-trace TSC matrix | Tests TSC across 30 paired operating conditions. |

## Results to remember

- Original primary baseline: 4,320 rows; 24 configurations; 30 paired seeds; six strategies.
- Original adaptive AHP selected 5G in all 5,768,175 recorded ranking calls; fixed 5G and adaptive AHP had identical primary results.
- TSC matrix: 30 conditions, 30 seeds each, 900 paired traces, 1,800 algorithm runs, 314,332 TSC decisions.
- TSC selector computation: significant reduction in 30/30 conditions; 72.31%–86.48% lower.
- Mean latency: significant reduction in 4/30 conditions. P95 latency: 3/30. Both concentrated in repeated-outage cases at 2–4 pps.
- Modelled energy: significant reduction in 2/30 4-pps repeated-outage cases, only 0.31%–0.38%; overall matrix total is 0.0736% higher for TSC.
- PDR and emergency PDR: no condition survives Holm correction.
- Packet-selection changes: 2,436 TSC vs 2,404 baseline; no reduced-switching claim.

## Likely questions and concise answers

**Q: What does “unifying 5G/6G with LPWAN” mean in your implementation?**
A: It is a gateway-centric logical integration. LoRaWAN is the access technology, and the gateway chooses a cellular backhaul. NB-IoT and 5G NR are simulated abstractions. A 6G profile is an architecture template only, not a 6G radio or core implementation.

**Q: What is actually new in your work?**
A: Not the individual algorithms. The project contribution is the specific gateway-side decision placement and coordinated pipeline, plus the two-timescale session/burst preference and packet-level override/fallback, evaluated across paired traffic/outage conditions.

**Q: Why add TSC if AHP-TOPSIS already works?**
A: The primary results revealed that adaptive AHP-TOPSIS chose 5G in every recorded ranking decision. TSC was added to test whether separating a session preference from packet-level decisions has operational value under changing availability.

**Q: Does TSC outperform AHP-TOPSIS?**
A: Not universally. It reduces selector computation time in all 30 conditions. It reduces mean latency in four and P95 latency in three repeated-outage conditions. It does not establish PDR or emergency-reliability improvement.

**Q: Does it save energy?**
A: Not overall. The aggregate modelled energy is slightly higher for TSC. Two conditions show small statistically significant reductions, but the model omits calibrated idle-tail and switching energy.

**Q: Does it reduce switching?**
A: Not demonstrated. The packet-selection change count is slightly higher for TSC. The current matrix tests binary outages rather than continuously varying signal quality.

**Q: Is the energy realistic?**
A: It is a modelled energy boundary including CPU, setup and transmit energy. It does not yet include calibrated modem sleep, idle-tail and switching energy. It is not hardware-measured.

**Q: Is 6G implemented?**
A: No. The software has a non-selectable IMT-2030 profile template and a technology-agnostic adapter contract. There is no 6G radio model, core, numeric profile or measured performance.

**Q: Why AHP? Are the weights validated?**
A: The state-specific weights are design-specified. The reciprocal pairwise matrix is generated from the weights, so consistency is by construction. An expert-elicitation study is future work.

**Q: What are the main limitations?**
A: Abstracted PHY/MAC and cellular core; no hardware; simplified traffic and energy models; no calibrated modem lifecycle profile; no probabilistic QoS guarantee; no complete 6G or standards-compliant interworking; limited trace duration and outage patterns.

## Claims to avoid

- Do not say “we implemented 6G.”
- Do not say “first-ever” or “novel AHP/TOPSIS algorithm.”
- Do not say TSC universally outperforms the baseline.
- Do not claim improved PDR, emergency reliability, reduced switching or overall energy saving.
- Do not call the fixed-NB-IoT vs adaptive-AHP comparison a physical before/after deployment.

## Foundational technical viva questions

**Q: What is LPWAN?**  
A: A Low-Power Wide-Area Network connects low-power devices over long distances using relatively low data rates. LoRaWAN is the access technology represented in this project.

**Q: Why combine LPWAN access with a cellular backhaul?**  
A: LoRaWAN provides a low-power access path for sensor traffic. A gateway can aggregate that traffic and use a cellular backhaul for onward transport, while keeping the more complex backhaul decision at the gateway rather than on each constrained endpoint.

**Q: Why is NB-IoT not treated as 5G NR?**  
A: NB-IoT originated in the LTE ecosystem and is modelled here as an LTE/EPC-style cellular LPWAN path. It is a distinct radio technology from 5G NR.

**Q: Why place the decision at an edge gateway?**  
A: The gateway has more processing capacity and a view of aggregated traffic and modem state. It can make the backhaul choice without requiring every sensor to maintain multiple cellular radios.

**Q: What does AHP do?**  
A: The Analytic Hierarchy Process converts pairwise criterion preferences into a normalized weight vector. In this project, the reciprocal pairwise matrix is generated from design-specified state weights, so its consistency is by construction rather than independent expert elicitation.

**Q: What does TOPSIS do?**  
A: TOPSIS normalizes and weights the feasible alternatives, identifies ideal-best and ideal-worst points, computes each candidate's distance from them, and ranks candidates using their relative closeness to the ideal.

**Q: Why filter feasibility before TOPSIS?**  
A: Availability and packet-deadline constraints are hard requirements. A candidate that is unavailable or cannot meet the packet deadline should not win because of a favourable score on another criterion.

**Q: Which criteria are used?**  
A: Latency and energy are cost criteria to minimize. Reliability and nominal bandwidth are benefit criteria to maximize.

**Q: Is this a machine-learning project?**  
A: No trained machine-learning model is used. AHP-TOPSIS and the Two-Timescale Controller are deterministic model-based decision methods; the EWMA and Poisson approximation are not learned predictors.

**Q: Why can the original adaptive AHP-TOPSIS match fixed 5G?**  
A: Under the configured candidate assumptions, 5G was selected in all 5,768,175 recorded primary ranking decisions. The five strategies that selected 5G therefore had identical packet-level outcomes in that operating point. This does not demonstrate adaptive AHP-TOPSIS superiority over fixed 5G.

**Q: What do PDR and latency mean in the reported results?**  
A: PDR is the fraction of generated packets delivered by the simulation horizon. Latency summaries are calculated over delivered packets. Packets still in flight at the horizon are not counted as delivered.

**Q: What does the separate 5G outage pilot show?**  
A: It is a five-seed functionality pilot showing NB-IoT selection while 5G is unavailable and a return to 5G after recovery. Its small sample makes it supplementary behaviour evidence, not a broad statistical or standards-level handover claim.

