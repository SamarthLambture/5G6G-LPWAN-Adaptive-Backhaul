# Unified LPWAN–Cellular Backhaul Architecture

**Status:** implemented architecture contract for the existing NB-IoT and 5G NR simulation profiles; exploratory IMT-2030/6G profile only.

## 1. Meaning of “unifying” in this project

The project unifies technologies at the **gateway-side backhaul control and selection layer**. LoRaWAN remains the IoT access technology. The gateway receives/aggregates logical LoRaWAN-originated packets and chooses an onward cellular backhaul candidate using a common decision interface.

This does **not** implement LoRaWAN PHY/MAC interworking with a 3GPP core, a complete EPC/5GC, standardised 3GPP ATSSS, a 6G radio interface, or a physical modem deployment. The existing simulator abstracts these network functions.

## 2. Architecture

1. **LPWAN device/access domain:** LoRaWAN-originated telemetry and event packets. Detailed LoRa PHY/MAC, collisions and per-device airtime remain abstracted.
2. **Gateway aggregation and edge domain:** packet registry, classification, CPU queue, gateway state and packet metadata.
3. **Backhaul decision domain:** availability and deadline feasibility, AHP/TOPSIS baseline or Two-Timescale Controller, and decision audit trail.
4. **Technology adapter domain:** one adapter per registered candidate. Adapters expose a normalized profile identity and runtime metrics.
5. **Cellular backhaul/core domain:** currently two simulated candidates—NB-IoT-style and 5G-NR-style paths—to a logical application endpoint. A future IMT-2030 profile is recorded as an architecture template only.

See [`../figures/unified_backhaul_architecture.svg`](../assets/architecture/unified_backhaul_architecture.svg).

## 3. Normalized candidate contract

The selector should not need to know the protocol-specific implementation of a backhaul. It consumes a candidate index and a normalized context containing:

| Field | Meaning | Unit / type |
|---|---|---|
| `profile_id` | Stable technology-profile identity | string |
| `name` | Human-readable technology name | string |
| `available` | Candidate is currently available | Boolean |
| `latency_s` | Predicted packet service/queue delay used by the model | seconds |
| `reliability_pct` | Configured/modelled reliability | percent |
| `bandwidth_bps` | Candidate nominal capacity | bits/s |
| `tx_energy_j` | Estimated energy for this packet's transmission | joules |
| `setup_energy_j` | Configured setup energy | joules |
| `setup_energy_due_j` | Setup energy currently due (e.g. modem asleep) | joules |
| `tail_time_s` | Configured session/tail horizon | seconds |
| `modem_state` | Adapter's current modem state | string |
| `metric_provenance` | Evidence/assumption label for supplied values | string |

The contract is implemented in `Framework/src/core/backhaul_interface.py`. It contains:

- `BackhaulProfile`: protocol-independent identity, maturity and capability metadata.
- `RuntimeBackhaulMetrics`: validated per-decision metrics.
- `BackhaulAdapter`: expected adapter operations (`estimate_delay`, `estimate_energy`, `selection_energy_context`, `add_packet`, outage/recovery hooks).
- `BackhaulCatalog`: registration, maturity checks and candidate-context construction.

The TSC consumes candidate indices and normalized context. The gateway now builds its candidate matrix and candidate context from an adapter list; `a1` and `a2` remain compatibility aliases for archived experiment scripts. `EdgeGateway` also accepts an optional `backhaul_adapter_factory(env, gateway)` and a `BackhaulCatalog`, so an additional implemented adapter can be injected without changing the candidate-construction loop. The current experiment suite still requires the NB-IoT and 5G NR baseline profiles for legacy outage events and compatibility result columns; extra selectable profiles can be appended to the gateway decision path. A future third-profile study must also extend its per-profile energy, queue and selection reporting so that no adapter's contribution is omitted from aggregate experiment metrics.

## 4. Profiles and implementation maturity

| Profile | Registry status | Selectable in current SimPy model? | Evidence boundary |
|---|---|---:|---|
| NB-IoT | `implemented_simulated` | Yes | Configured abstracted model; not physical measurement |
| 5G NR | `implemented_simulated` | Yes | Configured abstracted model; not physical measurement |
| IMT-2030 / 6G | `exploratory_template` | No | Capability tags only; no numeric radio metrics or radio/core model |

The current registry is deliberately conservative. Registering an exploratory profile does not make it selectable. A profile must have an implemented adapter and defensible model inputs before it can participate in performance experiments.

## 5. IMT-2030 capability tags

The exploratory profile records the six IMT-2030 usage-scenario labels described in ITU-R M.2160 and the ITU IMT-2030 work programme:

- Immersive communication (IC)
- Hyper-reliable and low-latency communication (HRLLC)
- Massive communication (MC)
- Ubiquitous connectivity (UC)
- Artificial intelligence and communication (AIAC)
- Integrated sensing and communication (ISAC)

These are **capability/use-case tags**, not numeric service guarantees. The project does not infer a particular 6G latency, throughput, reliability, spectral efficiency or energy value from these labels.

## 6. How a future 6G adapter would be added

Before an IMT-2030 profile could be selected in a simulator, the project would need:

1. A clearly identified candidate radio/interface profile and evaluation assumptions.
2. A runtime adapter implementing the `BackhaulAdapter` contract.
3. Candidate latency, capacity, reliability and availability models with documented sources.
4. A lifecycle-energy state model with explicit measurement boundaries.
5. Queue, outage, recovery and packet-delivery semantics compatible with the simulator.
6. Unit tests, integration tests and sensitivity ranges.
7. A new baseline comparison with identical event traces and appropriately scoped conclusions.

Until these requirements are met, the 6G profile stays excluded from normal simulation selection.

## 7. What the architecture readiness check establishes

Run from `Framework/`:

```bash
python experiments/audit_backhaul_extensibility.py
```

The script writes:

- `results/supplementary/backhaul_architecture/architecture_readiness.json`
- `results/supplementary/backhaul_architecture/backhaul_profile_catalog.csv`

It checks the registered profile maturity and runs a synthetic three-candidate selector-contract probe. The synthetic third candidate only establishes that the selector accepts an additional candidate index. It is **not** an IMT-2030 model, radio simulation, or performance result.

## 8. Standards and maturity note (21 November 2026)

ITU-R Recommendation M.2160-0 (November 2023) establishes the IMT-2030 framework and its envisaged usage scenarios. As reflected on the ITU's IMT-2030 pages on 21 November 2026, WP 5D had completed draft technical performance requirements in February 2026, draft evaluation guidelines in June 2026, and draft requirements/evaluation/submission-process material in October 2026; those drafts were listed for Study Group 5 approval in December 2026. The ITU page states that candidate RIT/SRIT submissions are expected to begin at the February 2027 WP 5D meeting.

Official references:

- [ITU-R Recommendation M.2160-0](https://www.itu.int/rec/R-REC-M.2160/en)
- [ITU IMT-2030 programme and current status](https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/pages/default.aspx)
- [ITU IMT-2030 submission and evaluation process](https://www.itu.int/en/ITU-R/study-groups/rsg5/rwp5d/imt-2030/Pages/submission-eval.aspx)

This is why the project represents 6G as an exploratory capability profile rather than claiming a deployed or finalized 6G radio implementation.

## 9. Exact claim we can defend

> The project implements a technology-profile-based gateway backhaul selection architecture with runnable NB-IoT-style and 5G-NR-style simulation adapters. Its normalized candidate interface and profile catalog provide an explicit extension point for future IMT-2030 technologies. The IMT-2030 entry is exploratory and is not used as a selectable radio candidate or as a source of performance results.

Do not claim that this project implements 6G, integrates a 6G core, or validates IMT-2030 performance.
