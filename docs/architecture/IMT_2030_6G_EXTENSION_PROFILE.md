# IMT-2030 / 6G Extension Profile

**Classification:** Exploratory architecture profile only; not a simulated 6G technology.

## Why a 6G profile is included

The professor's project brief asks for “unifying 5G/6G with LPWAN”. The existing runnable simulation covers LoRaWAN-originated traffic with NB-IoT and 5G NR-style cellular backhaul candidates. To make the architecture extensible without overstating implementation, the backhaul catalog now includes an IMT-2030 profile marked `exploratory_template` and `selection_enabled: false`.

## Capability vocabulary

The profile stores the six IMT-2030 usage scenarios from ITU-R M.2160:

| Tag | ITU usage scenario | Interpretation in this project |
|---|---|---|
| `immersive_communication` | IC | Future scenario label; no performance parameter assigned |
| `hyper_reliable_low_latency_communication` | HRLLC | Future scenario label; no latency/reliability value assigned |
| `massive_communication` | MC | Future scenario label; no device-capacity value assigned |
| `ubiquitous_connectivity` | UC | Future scenario label; no coverage value assigned |
| `ai_and_communication` | AIAC | Future scenario label; no AI-native radio feature modelled |
| `integrated_sensing_and_communication` | ISAC | Future scenario label; no sensing/radio modelled |

The profile also notes high-level design principles: security and resilience, connecting the unconnected, ubiquitous intelligence and sustainability. These are descriptive tags only.

## No invented 6G numbers

The profile deliberately has no numeric latency, bandwidth, reliability, setup-energy, idle-energy or switching values. No “6G” entry is added to the current SimPy gateway candidate list. No 6G performance claims may be inferred from the capability tags.

## Current ITU status on 21 November 2026

- ITU-R M.2160-0 was approved in November 2023 and describes the IMT-2030 framework and objectives.
- ITU-R WP 5D completed draft minimum technical performance requirements in February 2026.
- WP 5D completed draft evaluation guidelines in June 2026.
- WP 5D completed draft requirements/evaluation/submission-process material in October 2026, with submission to Study Group 5 for approval in December 2026.
- The ITU schedule indicates the first candidate RIT/SRIT submission phase begins in February 2027.

Therefore, on the audit date, it would be inaccurate to present the IMT-2030 exploratory profile as a finalized 6G radio interface.

Official sources:

- https://www.itu.int/rec/R-REC-M.2160/en
- https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/pages/default.aspx
- https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/Pages/submission-eval.aspx

## Promotion criteria

A future profile may only move from exploratory to simulation-selectable after all of the following exist:

1. Identified, versioned technical specification or explicitly scoped research proposal.
2. Sourced channel/service parameter set.
3. Radio and queue/service model with documented assumptions.
4. Lifecycle energy profile with a stated measurement boundary.
5. Availability and outage/recovery model.
6. Adapter implementation and reproducibility tests.
7. Paired evaluation against NB-IoT and 5G NR with suitable baselines.

Until then, the catalog correctly blocks the profile from normal simulation selection.
