# Change Log


> **Documentation consolidation note (17 November 2026):** entries below preserve historical filenames from earlier package revisions. The current repository consolidates those documents into `README.md` and the small set of references under `docs/`; historical filenames listed here are not separate files in this release.

**Working rule:** the original `CN_5G6G_LPWAN.zip` archive was not overwritten. All edits were made in a new working copy and packaged separately.

## A. Original archive vs prepared revision

Comparing project files while excluding `.venv`, Python caches and pytest caches:
- Original project snapshot: 45 files.
- Prepared revision: 68 functional/project files.
- Functional files added: 23.
- Existing same-path files changed: 10.
- Functional files removed: 0.

### Existing files changed in the prepared revision

| File | Change and rationale | Validation |
|---|---|---|
| `src/core/math_engine.py` | Added AHP/TOPSIS input validation, explicit RI values, principal-eigenvalue CR and tie handling while preserving valid project weights/decisions. | 20-test suite passed; four state matrices audited. |
| `src/core/algorithms.py` | Cached state weights to avoid repeated AHP matrix calculation. | Full suite passed; primary selection output audited. |
| `src/simulation/network.py` | Added 5G outage and recovery event handling in the existing network abstraction. | Outage tests passed; supplementary pilot rerun. |
| `tests/test_suite.py` | Added tests for 5G outage event/recovery and adaptive fallback/reselection. | 10 tests in this file passed. |
| `experiments/generate_figures.py` | Prepared revision added outage plot logic but initially read the outage scenario from the primary CSV, where it is intentionally absent. Final audit corrected it to read the separate supplementary pilot file. | Regenerated all 8 figures successfully. |
| `README.md` | Expanded framework, algorithm, weights, assumptions, result status and limitations. | Reviewed and extended with cross-platform instructions/test environment. |
| `FINAL_TECHNICAL_REVIEW.md` | Added results interpretation and limitations. | Stale test/outage statements corrected in audited revision. |
| `BUILD_NOTES.md` | Recorded build changes and early validation limits. | Rewritten to report actual independent validation. |
| `REVIEW_README.txt` | Review/readme changes. | Retained from prepared revision. |
| `results/raw/smoke_test_metrics.csv` | Smoke-test output snapshot. | New smoke run completed 6 strategy records; primary raw dataset not changed. |

### Functional files added in the prepared revision

| Added path | Purpose / validation |
|---|---|
| `IMPROVEMENT_ACTION_PLAN.md` | Documents targeted changes, commands and reporting guardrails; updated to completed audit status. |
| `experiments/audit_existing_results.py` | Rebuilds AHP, dominance, candidate-input and paired FDR diagnostics from archived data; rerun successfully. |
| `experiments/run_5g_outage_supplementary.py` | Runs separate five-seed outage/recovery pilot; independently rerun for 30 records. |
| `results/REPRODUCIBLE_PROJECT_DIAGNOSTICS.md` | Human-readable primary data diagnostics. |
| `results/figures/08_5g_outage_failover.png` | Supplementary outage figure, regenerated from separate pilot data. |
| `results/raw/smoke_test_5g_outage_metrics.csv` | Outage smoke-test evidence. |
| `results/supplementary/5g_outage/metadata.json` | Pilot configuration/metadata. |
| `results/supplementary/5g_outage/raw_metrics.csv` | 30 pilot raw records; independent rerun matched. |
| `results/supplementary/5g_outage/summary.csv` | Six strategy summaries; independent rerun matched. |
| `results/supplementary/5g_outage/selection_summary.csv` | Fallback/recovery/switch metrics; independent rerun matched. |
| `results/supplementary/5g_outage/paired_vs_fixed5g.csv` | Paired comparison table; independent rerun matched. |
| `results/supplementary/5g_outage/seed_1000.csv` … `seed_1004.csv` | Per-seed checkpoints/output detail. |
| `results/tables/ahp_consistency_validation.csv` | AHP consistency audit. |
| `results/tables/baseline_candidate_decision_inputs.csv` | Candidate metrics explaining 5G selection dominance. |
| `results/tables/paired_statistics_bh_fdr.csv` | BH-FDR-adjusted paired statistics/effect sizes, supplementary to original unadjusted file. |
| `results/tables/selection_dominance_by_scenario.csv` | Pareto/feasibility counts by scenario. |
| `results/tables/selection_dominance_by_state.csv` | Pareto/feasibility counts by AHP state. |
| `tests/test_math_engine_standalone.py` | Standalone AHP/TOPSIS tests; seven tests pass. |
| `tests/test_audit_statistics_standalone.py` | Standalone BH-FDR tests; three tests pass. |

## B. Additional changes made in this final audited package

### Simulation and figure assets

| File | Final change | Validation |
|---|---|---|
| `experiments/generate_figures.py` | Corrected supplementary pilot source path; prevents mixing pilot rows into primary CSV. | Script completed; 7 primary + 1 supplementary figure generated. |
| `framework_architecture.png` | Replaced with an explicit five-layer diagram: solid simulated flow, dashed abstractions, dotted 6G future-work element. | Visually inspected. |
| `5G6G_LPWAN_Final_Figures/framework_architecture.png` | Synced with the updated architecture diagram. | Visually inspected. |
| `results/figures/08_5g_outage_failover.png` | Regenerated using separate pilot file. | Visually inspected. |
| `results/tables/5g_outage_summary.csv` | Generated by the corrected figure/report script. | Cross-checked against pilot source data. |

### Project documentation

- `README.md` — added Windows PowerShell and Linux/macOS setup and run instructions, test environment and separate-pilot cautions.
- `FINAL_TECHNICAL_REVIEW.md` — corrected test count, figure count, 5G pilot status, FDR scope and final findings.
- `BUILD_NOTES.md` — rewritten as a final validation record.
- `IMPROVEMENT_ACTION_PLAN.md` — marked as completed and clarified target-machine validation.
- `Demo_and_Viva_Notes.txt` — corrected test/outage statements and added pilot discussion.
- `5G6G_LPWAN_Conventional_College_Project_Report.docx` — corrected test count and outage scope; added pilot results and figure; updated architecture asset.
- `5G6G_LPWAN_IEEE_Style_Research_Paper.docx` — corrected scenario/test/limitation language and added pilot result summary; updated architecture asset.
- `5G6G_LPWAN_Final_Research_Report_Draft.docx` — corrected test count/outage scope and added pilot result context.
- `5G6G_LPWAN_Project_Presentation.pptx` — updated limitations/conclusions, added Pareto/statistical interpretation slides, and replaced the oversized slide-5 raster process image with an editable seven-stage two-row flowchart. The final 18-slide deck passes the slide-canvas overflow test.
- Cross-document layer consistency — corrected the ordering of edge management/orchestration (layer 3) and cellular backhaul/core (layer 4) in the README, technical review, college/draft report tables, IEEE-style paper and viva notes.
- `Demo_and_Viva_Notes_Final.txt` — corrected test/outage status and added pilot metrics.
- `FINAL_SUBMISSION_README.txt` — replaced stale 4500-row plan with the verified 4320-row primary + 30-row supplementary scope and run commands.
- `REVISION_GUIDE.md` — corrected test environment wording and clarified independent pilot reproduction.

### New top-level audit deliverables

- `EXECUTIVE_TECHNICAL_AUDIT.md`
- `TEST_REPORT.md`
- `EXPERIMENT_REPORT.md`
- `CHANGELOG.md`
- `REMAINING_WORK_CHECKLIST.md`
- `START_HERE.md`

## C. Validation status

- Full pytest: **25 passed, 0 failed, 0 skipped**.
- Smoke simulation: **6/6 strategies completed**.
- Primary dataset integrity: passed row-count, uniqueness, missingness and energy-accounting checks.
- Supplementary outage pilot: **30/30 records regenerated; four main CSVs matched exactly**.
- Figure generation: **8 figures generated**.
- Original full 4,320-run simulation: not rerun; archived data audited.
- Windows execution: still to be performed on the user's target machine using a fresh OS-native virtual environment.


## D. Final inference and documentation corrections (14 November 2026)

| File / area | Change | Evidence / validation |
|---|---|---|
| `src/core/paired_statistics.py` | Added a shared paired t-test helper that preserves descriptive paired differences but returns NaN inferential fields for zero variance or insufficient samples; adds Shapiro-Wilk and Wilcoxon diagnostics. | Five new tests; complete suite 25/25 passed. |
| `experiments/run_experiments.py` | Uses the shared helper in future primary runs, preventing artificial p = 1.0 values and zero-width intervals for zero-variance comparisons. | Compilation and unit tests passed. Full primary experiment intentionally not rerun. |
| `experiments/audit_existing_results.py` | Regenerates paired statistics and separate BH-FDR tables from the archived primary raw CSV; validates row/key counts, 60 emergency-latency NaNs and 5,768,175 AHP ranking calls. | Audit script completed successfully. Primary raw CSV retained. |
| `experiments/run_5g_outage_supplementary.py` | Uses shared paired inference; emits Wilcoxon/Shapiro fields and leaves zero-SD confidence bounds undefined. | Clean 30-run pilot completed; seed/raw/selection data matched prior pilot. Derived summary and paired file updated intentionally. |
| `experiments/generate_figures.py` | Reports undefined confidence intervals for zero-SD groups and reads the pilot from its separate file. | Eight figures generated. |
| College report, IEEE paper, report draft, README, diagnostics and viva | Added paired inference, Pareto denominator/criteria, 60-NaN explanation, standards boundaries and final counts. | Text consistency checks and DOCX rendering performed before packaging. |
| PowerPoint | Added Pareto/decision-input and statistical safeguards slides; updated scope and standards references. | 18-slide deck exported and rendered for visual inspection. |

The latest external standards references used in the final documents are TS 23.501 v19.9.0 (Release 19, published 2 October 2026), TS 23.503 v19.8.0 (Release 19, published 20 July 2026), and ITU-R Recommendation M.2160-0. Their descriptions are contextual; the project does not implement N3IWF, ATSSS, or 6G.


## E. Final visual and consistency QA corrections (14 November 2026)

- `5G6G_LPWAN_Project_Presentation.pptx`: replaced slide 5's over-height process diagram with an editable two-row seven-stage flow; verified the 18-slide deck with `slides_test.py` (no overflow).
- `5G6G_LPWAN_IEEE_Style_Research_Paper.docx`: consolidated author/affiliation data into one explicit placeholder row and restored sequential order of references [11] and [12]; rerendered and visually checked all four pages.
- `5G6G_LPWAN_Final_Research_Report_Draft.docx`: replaced the stale eight-test appendix statement with the verified 25-test Linux result and explicit pending Windows-validation status; rerendered and checked all twelve pages.
- `TEST_REPORT.md`: updated the final pytest runtime to the latest rerun (25 passed in 0.77 s).
- All final academic DOCX outputs were rendered for visual QA; updated statistics/appendix pages were inspected. The college report is 24 pages, IEEE paper 4 pages, and research-report draft 12 pages.


## F. Final packaging verification (14 November 2026)

- Re-ran the full test suite from the packaged project root: `25 passed, 0 failed, 0 skipped` (Python 3.13.5; pytest 9.0.2; SimPy 4.1.2 supplied from the original archive).
- Re-ran `compileall`, the six-strategy smoke test, the primary-data audit and the eight-figure generation.
- Replayed the supplementary outage pilot from a clean clone: 30 simulations; all five seed CSVs and the four aggregate CSV outputs matched the packaged pilot exactly.
- Rechecked the primary raw matrix against the prepared revision by SHA-256; it is byte-for-byte unchanged.
- Re-rendered the college report (24 pages), IEEE-style paper (4 pages), report draft (12 pages), and 18-slide deck; `slides_test.py` found no overflow.
- Synchronized current derived tables and eight generated figures into the documentation bundle; root-level DOCX copies now match the final documentation copies.
- Added `FINAL_EXECUTION_GUIDE.md` and a refreshed package manifest. Native Windows execution, institutional details and the full primary rerun remain explicitly pending/not claimed.

## 20 November 2026 — Two-timescale adaptive backhaul research upgrade

- Added `Framework/src/core/two_timescale.py` with a gateway-level session/burst preference controller and packet-level emergency QoS overrides.
- Added configurable setup-energy amortization, optional explicit idle-power and switching-energy sensitivity terms, EWMA arrival-rate estimation, Poisson burst-size estimation, dwell-time/improvement hysteresis, forced fallback and decision explainability.
- Integrated the controller into `Framework/src/simulation/network.py` without changing the legacy selection call path for the six existing strategies.
- Exposed the new `TSC` method through the optional FastAPI bridge; the browser-only simplified demonstration remains six-strategy and does not claim to implement TSC.
- Added deterministic controller tests, an analytical 72-row operating-region sweep and a short paired SimPy validation runner (prepared but not executed in this environment).
- Corrected stale CI, verifier, API and README source paths from nonexistent lowercase `simulation/` and `application/` directories to canonical `Framework/` and `Simulation/` directories.
- Added research-upgrade documentation for the audit, method, experiments, results/limitations, contribution/related work and reproducibility.
- Preserved all historical primary and supplementary experiment files; no full primary experiment was rerun.


## 20 November 2026 — 30-seed TSC validation and final research documentation

- Executed the paired 30-seed targeted SimPy comparison on the user's machine (120 s/seed, 2 packets/s, 10% emergency traffic, 5G outage from 40–60 s); 4.080 s measured wall-clock runtime.
- Added the supplied raw metrics and decision logs, run metadata, per-seed paired differences, Wilcoxon tests, Holm correction, aggregate summary and plots under `Framework/results/supplementary/two_timescale/30_seed_evaluation/`.
- Documented the narrow supported finding: lower mean/P95 latency and selector computation time in this single targeted configuration; PDR increase does not survive Holm correction, emergency PDR is unchanged, energy is slightly higher without significant difference, and reduced switching is not demonstrated.
- Updated the README and handoff so they report the completed 30-seed experiment rather than incorrectly describing the SimPy run as pending.
- Added `docs/research_upgrade/PROFESSOR_BRIEF.md` with a one-minute project explanation, verified numbers, limitations, likely viva questions and a demonstration plan.
- Preserved the original 4,320-row primary matrix and historical outage pilot. No original long-duration baseline was rerun.


## 20 November 2026 — Follow-up multi-operating-point evaluation tooling

- Added `Framework/experiments/run_two_timescale_matrix.py` for paired evaluation across offered loads and emergency traffic mixes. It checkpoints each completed condition, records metadata, preserves historical results and enforces a 900-second runtime budget.
- Added `Framework/experiments/analyze_two_timescale_matrix.py` for condition-wise paired inference, Holm correction across all metric/condition tests, aggregate tables and trend plots.
- Added deterministic tests for matrix analysis and its multiple-testing correction. The runner is prepared but has not been executed because SimPy is unavailable in this build workspace; do not treat its output as completed evidence.


## 20 November 2026 — Multi-operating-point matrix extended with outage patterns

- Expanded the bounded paired matrix to include no-outage, single-outage and repeated-outage conditions in addition to five offered loads and two emergency traffic shares (30 conditions, 900 paired traces with 30 seeds each).
- Extended the matrix analyzer to stratify by outage pattern and apply Holm correction across all metric × condition tests. The experiment remains prepared but unexecuted; its output must be generated before citing any matrix result.


## Submission packaging update — 21 November 2026

- Rebuilt the root README around the final project scope, implementation, baseline and TSC matrix evidence.
- Updated the browser Simulation README and refreshed contribution/performance-impact documentation.
- Added submission report, research-paper draft, reference comparison, baseline-vs-upgrade table, results/limitations and viva guide.
- Added high-resolution charts for baseline, TSC matrix, significant repeated-outage latency and selector-time results.
- Kept NB-IoT and 5G NR as simulated selectable profiles; IMT-2030/6G remains a non-selectable architecture template.
