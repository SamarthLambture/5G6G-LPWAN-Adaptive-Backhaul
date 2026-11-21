# Final Submission Package Manifest

**Project:** Unifying 5G/6G with LPWAN — Adaptive Edge-Gateway Backhaul-Selection Framework  
**Institution:** Indian Institute of Information Technology Raichur  
**Submission package date:** 21 November 2026

## Package contents

| Component | Location | Contents |
|---|---|---|
| Python research framework | `Framework/` | Source code, baseline and TSC algorithms, SimPy gateway simulation, tests, experiment scripts, raw/processed data, decision logs and figures |
| Browser simulation/demo | `Simulation/` | Frontend, optional FastAPI bridge, demo engine, run scripts and browser tests |
| Root overview | `README.md` | Project scope, architecture, complete baseline comparison, TSC results, limitations and setup commands |
| Technical documentation | `docs/` | Architecture, design, technical review, experiments, changelog and validation |
| Submission documentation | `docs/` | Topic-organized architecture, research, results, reproducibility and demo documentation; indexed by `docs/README.md` |
| Final report | `deliverables/FINAL_PROJECT_REPORT.*` | Editable DOCX and 19-page PDF; includes appendices A–E |
| Research paper draft | `deliverables/RESEARCH_PAPER_DRAFT.*` | Editable DOCX and 9-page faculty-review PDF; includes supplementary baseline and related-work appendices |
| Presentation | `deliverables/FINAL_PROJECT_PRESENTATION.*` | Editable PPTX and 21-slide PDF; includes five supplementary comparison/reference slides |
| Research-upgrade evidence | `Framework/results/supplementary/two_timescale/` | Smoke validation, 30-seed test, 900-trace matrix, raw decision logs, metadata, statistics and plots |
| Integrity manifest | `SHA256SUMS.txt` | SHA-256 checksums for package files (excluding this manifest itself) |

## Comparison content included

- Complete six-strategy original baseline table for the A_NORMAL operating point (30 seeds per strategy).
- Baseline-versus-upgrade feature traceability table, with evidence boundaries and limitations.
- Separate TSC 900-trace comparison: 30 operating conditions, 900 paired traces, 1,800 algorithm-run records and 314,332 TSC decision records.
- Condition-wise statistical findings using paired Wilcoxon tests with Holm correction across 180 comparisons.
- Paper-by-paper comparison tables covering research objectives, methods/evaluation, reported evidence, overlap and differences.
- Embedded figures and charts placed adjacent to the relevant report/paper sections and supplementary presentation slides.

## Evidence and scope boundaries

- The original primary experiment contains 4,320 metric rows across 24 configurations, 30 seeds and six strategies.
- The separate TSC matrix contains 30 conditions and 900 paired input traces. It is not the same experiment as the original 3,600-second primary matrix.
- The simulation represents LoRaWAN-originated traffic and logical NB-IoT/5G NR backhaul candidates. It is not a physical radio deployment or standards-complete interworking implementation.
- The IMT-2030/6G profile is non-selectable and has no numeric radio capability model or performance results.
- The research paper is a student draft for faculty review, not a peer-reviewed publication.
- The literature comparison is representative, not a systematic review, patent search or proof of first-of-its-kind priority. Access limitations are documented.

## Final document pagination

- `FINAL_PROJECT_REPORT.pdf`: 19 pages; complete baseline and related-work appendices A–E.
- `RESEARCH_PAPER_DRAFT.pdf`: 9 pages; faculty-review appendices A–B.
- `FINAL_PROJECT_PRESENTATION.pdf`: 21 slides; original presentation plus five supplementary comparison/reference slides.

## Before departmental upload

1. Verify student names and roll numbers against official institute records. The package currently reflects the roll numbers present in the supplied project report.
2. Add faculty-guide name, academic year/session, declarations, certificates and signatures if required by the department. These were not supplied and have not been invented.
3. Open the final PDFs and editable files on the target computer.
4. Run the Python tests from `Framework/` in the team's Windows environment after installing `Framework/requirements.txt`. A build environment without SimPy cannot collect the SimPy-dependent test module.
5. Run the Simulation verifier and browser tests in the target environment.
6. Do not claim actual 6G implementation, hardware deployment, full 3GPP interworking, universal performance improvement, statistically significant PDR/emergency-reliability gains, reduced switching or overall energy savings.
