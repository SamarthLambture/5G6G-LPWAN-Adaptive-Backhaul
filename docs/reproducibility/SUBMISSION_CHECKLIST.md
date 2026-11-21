# Final submission checklist

## Required review before upload

- [ ] Confirm team names and roll numbers on the report cover.
- [ ] Confirm whether the department requires a faculty-guide name, academic session, declaration or signature page; these were not supplied in the project files.
- [ ] Open the final PDF report, research-paper draft and presentation PDF/PowerPoint and inspect figures, tables and pagination.
- [ ] Confirm the final presentation is consistent with the report and does not claim physical 6G implementation.
- [ ] Run the Python tests from `Framework/` in the target Windows environment.
- [ ] Run the Simulation verifier and browser tests from `Simulation/`.
- [ ] Run `Framework/experiments/audit_backhaul_extensibility.py` and retain its JSON/report output.
- [ ] Do not claim physical deployment, complete 3GPP interworking, or actual 6G implementation.
- [ ] Preserve the distinction between the 4,320-row historical primary archive and the separate 900-trace TSC matrix.
- [ ] Describe the 900-trace performance result accurately: computation time improves in all 30 conditions; latency improves in selected repeated-outage cases; PDR/emergency PDR, lower switching and overall energy savings are not established.
- [ ] Keep the student research paper labelled as a draft for faculty review, not a peer-reviewed publication.

## Evidence files

- Original primary metrics: `Framework/results/raw/raw_paired_metrics.csv`
- TSC matrix summary and tests: `Framework/results/supplementary/two_timescale/multi_operating_point/`
- Statistical analysis: `matrix_paired_statistics.csv` and `DETAILED_MATRIX_ANALYSIS.md`
- Main report and paper: `deliverables/`
- Figures: `docs/assets/results/`


## Final cross-check additions (21 Nov 2026)
- [x] Complete six-strategy A_NORMAL baseline table included in the report supplementary appendices and presentation addendum.
- [x] Baseline-versus-upgrade feature traceability table included in the report and documentation.
- [x] TSC 900-trace aggregate and condition-wise statistical results included with explicit metric aggregation definitions.
- [x] Related-work matrix expanded to include methodology/evaluation, reported findings, overlap and project distinction.
- [x] New graphs embedded adjacent to the corresponding appendix tables/sections.
- [x] DOCX/PDF and PPTX/PDF submission documents regenerated and checked.
- [ ] Team roll numbers and faculty/session metadata must be verified against official institute records before upload.

## Final integrated submission pass (21 Nov 2026)
- [x] Final project report includes appendices A–E: six strategies, before/after traceability, TSC results, related-work methods/results/differences and claim boundaries.
- [x] Research paper draft includes full six-strategy baseline and expanded related-work appendices.
- [x] Presentation includes five supplementary slides with the complete baseline, implementation impact, paper comparisons and references.
- [x] Figures are embedded adjacent to the corresponding document sections and retained as source assets.
- [x] Updated PDFs regenerated from editable DOCX/PPTX sources: report 19 pages, paper 9 pages, presentation 21 slides.
- [x] Fast Python tests: 46 passed; browser/Node tests: 22 passed; repository verifier and adapter extensibility audit passed.
- [ ] Run the complete SimPy-dependent Python test module on the target Windows environment after installing Framework/requirements.txt; SimPy is absent from the current build container.
- [ ] Confirm official team roll numbers and add faculty/session/declaration pages if required.
