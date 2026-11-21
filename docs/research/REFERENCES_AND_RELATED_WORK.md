# References and selected related work

This is a focused, representative literature review, not a systematic review. Some conference records were available only as metadata/abstracts; this is identified below. The project-specific claims and all numerical results are sourced from the repository's archived CSV/JSON data and reports.

[1] O. D. D. Brito, P. Pace, and F. De Rango, “A Unified Backhaul Architecture for Seamless LoRaWAN IoT Integration in 5G NR Networks,” IEEE PIMRC, 2026. DOI: 10.1109/PIMRC69400.2026.11711913. Abstract/metadata reviewed; full text was not accessible during this audit.

[2] S. Ghadimi, T. D. Le, M. Stusek, D. Moltchanov, P. Masek, and J. Hosek et al., “Adaptive Load Balancing and Hybrid Scheduling for Energy-Efficient NB-IoT Operation in Integrated Terrestrial–Non-Terrestrial Networks,” Internet of Things, vol. 40, art. 102151, Nov. 2026. DOI: 10.1016/j.iot.2026.102151. Abstract and indexed record reviewed.

[3] K. Usman, A. L. de Oliveira, C. E. Pereira, et al., “Adaptive physical-layer optimization in LoRa via weighted moving average and low-pass filter,” Annals of Telecommunications, published 18 Nov. 2026. DOI: 10.1007/s12243-026-01235-z.

[4] D. Roy, A. Das, and D. Saha, “Fuzzy-AHP-Based Network Selection in HetNet: An Energy-Efficient and QoS-Aware Approach,” IEEE Transactions on Green Communications and Networking, vol. 10, pp. 1404–1418, 2026. DOI: 10.1109/TGCN.2025.3632392.

[5] R. Možný, P. Masek, D. Moltchanov, M. Stusek, P. Mlynek, Y. Koucheryavy, and J. Hosek, “Characterizing optimal LPWAN access delay in massive multi-RAT smart grid deployments,” Internet of Things, vol. 25, art. 101001, 2024. DOI: 10.1016/j.iot.2023.101001.

[6] T. Shahgholi, A. Sheikhahmadi, K. Khamforoosh, et al., “LPWAN-based hybrid backhaul communication for intelligent transportation systems: architecture and performance evaluation,” EURASIP Journal on Wireless Communications and Networking, 2021, art. 35. DOI: 10.1186/s13638-021-01918-2.

[7] Y. Chen, Y. A. Sambo, O. Onireti, S. Ansari, and M. A. Imran, “LoRaWAN-5G Integrated Network With Collaborative RAN and Converged Core Network,” IEEE PIMRC, 2022. DOI: 10.1109/PIMRC54779.2022.9977480.

[8] G. Leenders, G. Callebaut, G. Ottoy, L. Van der Perre, and L. De Strycker, “Multi-RAT for IoT: The Potential in Combining LoRaWAN and NB-IoT,” IEEE Communications Magazine, vol. 59, no. 12, pp. 98–104, 2021. DOI: 10.1109/MCOM.008.2100382.

[9] V. Skrastins, V. Medvedevs, D. Orlovs, J. Ormanis, and J. Judvaitis, “Experimental Evaluation of NB-IoT Power Consumption and Energy Source Feasibility for Long-Term IoT Deployments,” IoT, vol. 7, no. 1, art. 7, 2026. DOI: 10.3390/iot7010007.

[10] M. Uitto, J. Mäkelä, O. Apilo, S. J. Rantala, J. Pinola, et al., “Study and analysis of runtime energy consumption in cellular 5G network: an empirical approach,” Journal on Wireless Communications and Networking, 2026, art. 57. DOI: 10.1186/s13638-026-02598-6.

[11] “Delay-Aware Dual-Interface Gateway Activation for Energy-Efficient Data Collection in IoT,” IEEE Transactions on Green Communications and Networking, vol. 9, no. 3, pp. 1064–1078, Sep. 2025. DOI: 10.1109/TGCN.2024.3510012.

[12] ITU-R, Recommendation M.2160-0, “Framework and overall objectives of the future development of IMT for 2030 and beyond,” 2023. https://www.itu.int/rec/R-REC-M.2160/en.

[13] ITU-R Working Party 5D, IMT-2030 programme status page, accessed 21 Nov. 2026. https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/pages/default.aspx.

## Why these papers matter

| Ref. | Research focus | Relevance / boundary for this project |
|---|---|---|
| [1] | Unified LoRaWAN–5G NR backhaul architecture, UDP/IP encapsulation and 5G slicing/coexistence coordination. | Closest recent architectural competitor. Its focus is seamless integration and coexistence; our work focuses on gateway-side cellular backhaul choice. Full text was not available in this audit, so comparison is based on public abstract/metadata. |
| [2] | Adaptive terrestrial/non-terrestrial NB-IoT assignment plus per-packet contention/grant scheduling. | Strong conceptual overlap with layered network assignment and packet scheduling. Different access/backhaul setup: TN/NTN, not a LoRaWAN gateway choosing NB-IoT vs 5G NR. |
| [3] | LoRa gateway WMA/LPF filtering of SNR to reduce physical-layer reconfiguration. | Establishes temporal smoothing and stable adaptation as prior art; our EWMA estimates traffic inter-arrival behaviour, not LoRa SNR. |
| [4] | Dynamic fuzzy-AHP QoS/energy network selection with TOPSIS/VIKOR comparisons. | Rules out novelty claims based solely on adaptive weighting or energy/QoS MCDM. |
| [5] | NB-IoT/LTE-M multi-RAT access association under polling/batch traffic. | Batch arrivals and multi-RAT load association are established; our decision point is the shared LoRaWAN gateway's cellular backhaul. |
| [6] | LTE-M/NB-IoT LPWAN-based hybrid backhaul for ITS and emergency/monitoring applications. | Cellular LPWAN as backhaul and mixed urgency have prior precedent; different application architecture and decision problem. |
| [7] | LoRaWAN–5G integrated network, collaborative RAN and converged core/testbed. | Confirms that LoRaWAN–5G integration is already demonstrated. Our simulator does not implement a converged core or physical testbed. |
| [8] | Multi-RAT IoT, combining LoRaWAN and NB-IoT at the IoT node. | Distinguishes node-level multi-radio integration from our gateway-side backhaul decision. |
| [9] | Measured NB-IoT device energy for payload, signal and temperature variations. | Supports the need for calibrated, condition-dependent modem energy profiles. |
| [10] | Empirical runtime 5G energy measurement across end devices, RAN and applications. | Demonstrates that 5G energy is device/system/configuration dependent and should not be represented by universal constants. |
| [11] | Delay-aware dual-interface gateway activation for energy-efficient IoT collection. | Adjacent gateway-side interface activation and energy-delay trade-off. |
| [12]–[13] | IMT-2030 framework and programme status. | Provides the standards boundary for treating the project's 6G profile as exploratory, not a 6G implementation. |

## Research gap interpretation

The reviewed literature establishes most individual ingredients: LoRaWAN–cellular integration, gateway/backhaul architectures, multi-RAT selection, AHP/TOPSIS, energy/QoS adaptation, traffic smoothing, batch-aware association, packet scheduling, and modem energy measurement. The defensible project contribution is narrower: a gateway-centred software framework coordinating (i) session/burst preference, (ii) packet-level emergency override, (iii) availability/QoS fallback, and (iv) an extensible backhaul-profile contract in a LoRaWAN-originated NB-IoT/5G NR simulation, evaluated on paired operating conditions. This is a system-level integration and evaluation contribution, not a new foundational algorithm.

No first-of-its-kind or state-of-the-art claim is made. A complete systematic review, citation chaining, and access to full IEEE/ACM/Scopus/Web of Science records would be needed before asserting priority.

## Additional adjacent literature reviewed for the novelty audit

[14] E. M. Torroglosa-Garcia et al., “Enabling Roaming across Heterogeneous IoT Wireless Networks: LoRaWAN meets 5G,” *IEEE Access*, vol. 8, 2020. DOI: 10.1109/ACCESS.2020.2998416. The accepted manuscript describes 5G-assisted LoRaWAN authentication/key management and a real integrated roaming testbed. This establishes that LoRaWAN/5G integration and roaming are prior art.

[15] “High-Availability in IoT Applications through Dual Connectivity: Integrating LoRaWAN and NB-IoT,” IEEE DRCN, 2024. DOI: 10.1109/DRCN60692.2024.10539139. The publicly accessible IEEE abstract describes a hardware prototype using dual LoRaWAN/NB-IoT connectivity and multipath routing for resilience. Abstract/metadata were reviewed; full text was not available during this audit.

[16] D. Orlovs, A. Rusins, V. Skrastins, and J. Judvaitis, “LPWAN Technologies for IoT: Real-World Deployment Performance and Practical Comparison,” *IoT*, vol. 6, no. 4, art. 77, 2025. DOI: 10.3390/iot6040077. This review of real-world deployments illustrates that practical range, battery life, reliability and scalability can diverge from vendor specifications. It motivates cautious model calibration rather than supplying directly transferable parameters.

[17] S. Tang, “Reliability-Aware Admission Threshold Selection for IoT Gateway–Cloud Systems: Trade-Off-Driven and Constraint-Based Approaches,” *IoT*, vol. 7, no. 3, art. 60, 2026. DOI: 10.3390/iot7030060. The work formulates reliability-aware admission in a finite-buffer gateway/cloud queueing model. It establishes queue reliability and admission control as adjacent prior art; the present project does not yet implement its own predictive queue-risk controller.

[18] Y. Kang, S. Kim, J. Kim, H. Ko, and Y. Kyung, “Reliability- and Latency-Aware ATSSS Framework for URLLC Services,” *Electronics*, vol. 15, no. 18, art. 4311, 2026. DOI: 10.3390/electronics15184311. The paper addresses reliability- and latency-constrained multi-access traffic steering. The full-page fetch was blocked during this audit; the abstract and available method/conclusion information were reviewed. It is adjacent multi-access prior art, not a direct LoRaWAN gateway competitor.

These additions broaden the related-work context but do not convert this document into a systematic review. Full-text access limitations are stated above; no first-of-its-kind or priority claim is made.


For the project-specific contribution, overlap boundaries and future research direction, see [Research Contribution](RESEARCH_CONTRIBUTION.md).


## 4. Consolidated comparison: methodology, reported evidence and project distinction

The following comparison is intentionally explicit about source-access limits. Numerical findings are reported only as the corresponding paper’s findings under its own test conditions; they are not directly compared as if they came from this project’s simulator.

### 4.1 Integration, cellular backhaul and multi-RAT

| Study | Methodology / evaluation | Reported result or evidence | Relevance and difference from this project |
|---|---|---|---|
| Brito et al. (2026) [1] | LoRa-NR frame adaptation, UDP/IP encapsulation, 5G slicing, Cognitive Spectrum Controller, OMNeT++ co-simulation described. | Abstract/repository record reports PDR above 91% versus an uncoordinated baseline; full paper not accessible in this review. | Establishes LoRaWAN–5G backhaul integration. Focus is protocol encapsulation, slicing and coexistence, not gateway choice between NB-IoT and 5G. |
| Chen et al. (2022) [7] | LoRaWAN–5G integrated network with collaborative RAN and converged core; testbed-oriented architecture. | Published architecture/testbed demonstration; no directly comparable numerical figure is used here. | Confirms LoRaWAN–5G integration is prior art. This project does not implement the converged core or collaborative RAN. |
| Shahgholi et al. (2021) [6] | ITS/fog backhaul using LTE-M/NB-IoT; SUMO maps for New York/Toronto and Python communication model, including emergency pre-emption. | Evaluated 1,000 and 2,000 vehicle settings; LTE-M showed lower latency than NB-IoT in reported scenarios. | Cellular LPWAN backhaul and urgent traffic are established. This project has LoRaWAN front-haul and shared gateway backhaul selection. |
| Možný et al. (2024) [5] | NB-IoT/LTE-M measurements plus analytical association model; periodic polling and batch traffic. | Under the paper’s assumptions, multi-RAT supports up to 3,000 devices under a 2-s mean access-delay budget versus 500 for LTE-M alone. | Batch traffic and multi-RAT association are known. Our decision boundary is a shared gateway’s outgoing cellular backhaul. |
| Leenders et al. (2021) [8] | Multi-RAT IoT analysis of combining LoRaWAN and NB-IoT. | Communications Magazine analysis; no comparable gateway-selection experiment quoted. | Combined LoRaWAN/NB-IoT is established. Our selected cellular backhaul candidates are NB-IoT and 5G NR after LoRaWAN aggregation. |

### 4.2 Network selection, hierarchical control, adaptation and energy

| Study | Methodology / evaluation | Reported result or evidence | Relevance and difference from this project |
|---|---|---|---|
| Ghadimi et al. (2026) [2] | Adaptive terrestrial/non-terrestrial NB-IoT assignment plus hybrid per-packet scheduling; 3GPP-aligned MATLAB Monte Carlo, 200 replications per operating point. | Trade-offs, not universal superiority; AHSA can be lower energy/delay in many conditions. Abstract/indexed record and substantial method/result details reviewed. | Closest conceptual overlap with hierarchical assignment/per-packet control; domain is TN/LEO-NTN NB-IoT, not LoRaWAN gateway NB-IoT/5G backhaul. |
| Roy et al. (2026) [4] | Fuzzy-AHP dynamic pairwise weighting for energy/QoS HetNet selection; compares AHP, TOPSIS and VIKOR. | Reports 11%, 33%, and 54% energy reductions for selected video, image and audio satisfaction configurations; full result tables not independently reviewed. | Energy/QoS MCDM is established; project does not claim AHP/TOPSIS or dynamic weighting as new. |
| Rahayani et al. (2026) | Dual-stage AHP-TOPSIS for AMI communication technology selection across five LPWAN options; sensitivity analysis. | LTE-M achieved the highest reported closeness coefficient (0.89) in the described case study. | Shows AHP-TOPSIS for LPWAN technology selection is known; this project applies gateway runtime selection to cellular backhaul candidates. |
| Usman et al. (2026) [3] | LoRa SNR adaptation using weighted moving average and low-pass filter with persistence-based trigger; controlled testbed. | Reported 5.65% fewer reconfigurations (WMA), 8.53% fewer band shifts (LPF) and 59.3% SNR gain after reconfiguration in the described setup. | Smoothing and stable adaptation are prior art; TSC EWMA estimates packet inter-arrival, not LoRa SNR. |
| Kang et al. (2026) | Reliability/latency-constrained ATSSS; constrained MDP and primal-dual DDQN for Wi-Fi/cellular steering or redundant transmission. | Reports cost/latency/reliability trade-offs; some joint targets are infeasible. | Reliability-constrained multi-access is established in URLLC; this project’s network boundary is LoRaWAN gateway cellular backhaul. |
| Skrastins et al. (2026) [9] | Commercial NB-IoT module power measurements across payload size, signal strength and temperature. | In that test configuration, 1,280-byte message used about seven times less energy per bit than 80-byte message; standby current 6.7–23 µA across tested devices. | Shows payload and standby state matter; values cannot be transplanted directly as universal simulator constants. |
| Uitto et al. (2026) [10] | Empirical live 4G/5G environment with UE/CPE/RAN energy instrumentation, traffic and idle measurements. | Energy varied with traffic, hardware and radio deployment; study emphasizes idle consumption and explicit measurement boundary. | Motivates lifecycle calibration; current project energy remains simulation-configured, not measured 5G modem/RAN energy. |
| DGA dual-interface gateway activation (2025) [11] | Delay-aware activation of higher-power Wi-Fi alongside low-power ZigBee; prototype-oriented evaluation. | Abstract reports up to 62.1% and 45.9% lower gateway energy versus selected baselines; full text not available in this review. | Gateway interface activation is prior art; ZigBee/Wi-Fi platform and energy boundaries differ from LoRaWAN/cellular gateway backhaul. |

**Comparability rule:** the cited studies use different hardware, topologies, traffic models, radio/core stacks, energy boundaries and evaluation metrics. Their numerical results are not direct benchmarks for the project’s simulator. Source-access limitations are stated where relevant.
