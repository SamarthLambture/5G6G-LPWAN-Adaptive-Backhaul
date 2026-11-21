# Final Submission QA Record

**Package build:** 21 November 2026  
**QA scope:** project files, final report, research-paper draft, presentation, experiment evidence and archive integrity.

## Final rendered documents

| Document | Editable source | Rendered PDF | Pages/slides |
|---|---|---|---:|
| Final project report | `deliverables/FINAL_PROJECT_REPORT.docx` | `deliverables/FINAL_PROJECT_REPORT.pdf` | 19 pages |
| Research paper draft (faculty review) | `deliverables/RESEARCH_PAPER_DRAFT.docx` | `deliverables/RESEARCH_PAPER_DRAFT.pdf` | 9 pages |
| Final presentation | `deliverables/FINAL_PROJECT_PRESENTATION.pptx` | `deliverables/FINAL_PROJECT_PRESENTATION.pdf` | 21 slides |

All three rendered documents were regenerated from the updated editable sources. The report includes supplementary comparative appendices A–E. The research-paper draft includes supplementary appendices A–B. The presentation contains five additional slides covering the full six-strategy baseline, baseline-to-upgrade traceability, two related-work comparison tables and additional references.

## Comparison coverage

- Complete six-strategy baseline table: included in the report and research-paper appendices and in the presentation addendum.
- Baseline-versus-upgrade feature traceability: included in the report, root README, comparison document and presentation.
- TSC 900-trace aggregate and condition-wise statistical evidence: included with explicit aggregation definitions, paired-test method and Holm correction.
- Related-work comparison: selected studies compared by methods/evaluation, reported evidence, overlap and project distinction. Access limitations are stated; results from different platforms are not treated as direct benchmarks.
- Figures: baseline, TSC, significant-latency and architecture images are embedded near their corresponding sections and retained in `docs/assets/results/`.
- Limitations and claims boundary: explicitly state no physical network deployment, no actual 6G implementation, no significant PDR/emergency-PDR gain, no switching-reduction result and no overall energy saving.

## Automated checks executed in the build environment

| Check | Result | Note |
|---|---|---|
| Fast Python tests | PASS: 46 tests | Ran `pytest tests -q --ignore=tests/test_suite.py` from `Framework/`. |
| SimPy-dependent test module | NOT COLLECTED | The build container does not have `simpy`; run full tests on the target machine after installing `Framework/requirements.txt`. |
| Browser/Node tests | PASS: 32 tests | Ran `node --test tests/*.test.cjs` from `Simulation/`. |
| Repository verifier | PASS | Validated original 4,320-row primary dataset structure, 24 scenarios, 30 seeds, six strategies and bundled Python source compilation. |
| Backhaul extensibility audit | PASS | Three-candidate interface probe passed using a synthetic third adapter; it is explicitly not 6G performance evidence. |
| PDF rendering | PASS | PDFs regenerated and page counts checked. Relevant report and appendix pages, paper appendices and presentation addendum were visually inspected. |

## Items the team must verify before official upload

1. Confirm team names and roll numbers against official institute records. The current documents use the roll numbers supplied in the project report; earlier materials had an Ayush Parde roll-number discrepancy.
2. Add the faculty guide, academic year/session, declarations, certificates or signatures if required by the department.
3. Run the complete SimPy-dependent Python test suite on the team's Windows environment after installing `Framework/requirements.txt`.

## Integrity

`SHA256SUMS.txt` contains per-file SHA-256 hashes for the package contents, excluding the checksum file itself. The ZIP archive was tested after creation.

## Documentation-cleanup verification (21 November 2026)

The final archive was checked after the repository documentation was reorganized. The `Framework/` and `Simulation/` directory trees were preserved byte-for-byte relative to the supplied archive.

| Check | Result | Notes |
|---|---|---|
| Framework non-SimPy test subset | PASS: 46 tests | `python -m pytest -q --ignore=tests/test_suite.py` from `Framework/`. |
| Browser/Node tests | PASS: 32 tests | `node --test tests/*.test.cjs` from `Simulation/`. |
| JavaScript syntax | PASS | `node --check frontend/app.js` and `node --check frontend/simulation-engine.js`. |
| Simulation verifier | PASS | `python verify_project.py` from `Simulation/`; validates the primary dataset and project assets. |
| Archive integrity | PASS | ZIP integrity check completed after packaging. |
| Full SimPy integration test module | NOT RUN | SimPy was not installed in the build environment; run the complete framework test suite after installing `Framework/requirements.txt`. |

The documentation cleanup changed no source, test, configuration, data or asset file under `Framework/` or `Simulation/`.
