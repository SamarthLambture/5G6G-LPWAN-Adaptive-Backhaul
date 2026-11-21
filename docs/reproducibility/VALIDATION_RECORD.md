# Validation and Test Record

This file consolidates Python, browser-application and packaging validation records. Historical records may report different test totals because the browser suite was expanded. The latest bundled application suite contains 19 Node tests; the Python simulator suite contains 25 tests in the project's validation record.

**Validation boundary:** the build environment used for this repository reorganisation does not have SimPy installed and cannot access PyPI. Consequently, Python test execution is not claimed as freshly rerun here. The user previously reported successful local Windows execution of the original project. Run the commands in the root README after extraction to validate the reorganised paths on your machine.

**Historical-status clarification:** the 13–14 November audit excerpts below predate this repository flattening and still say native Windows execution was pending at that time. The user subsequently reported successful Windows execution of the previous package layout. The current layout was not fully retested on Windows in this packaging environment; the local browser tests, project verifier, compilation and HTTP resource checks were run against the reorganised layout, plus 15 Python tests that do not require SimPy.

---

## Python project test report

# Test and Environment Report

**Audit date:** 14 November 2026  
**Result:** 25 passed, 0 failed, 0 skipped

## Environment used for validation

| Component | Version / configuration |
|---|---|
| Operating system | Linux audit container |
| Python | 3.13.5 |
| SimPy | 4.1.2 pure-Python source extracted from the supplied original archive |
| NumPy | 2.3.5 |
| Pandas | 2.2.3 |
| SciPy | 1.17.0 |
| Matplotlib | 3.10.8 |
| pytest | 9.0.2 |

The host Python environment did not have SimPy installed and package-network access was unavailable. The supplied original project archive contains a pure-Python SimPy 4.1.2 package, which was extracted to an isolated audit path and made available through `PYTHONPATH`. The bundled Windows virtual environment was not executed on Linux; its executables and binary packages are OS-specific.

## Full test suite

**Exact command executed from the project root on the audit host:**

```bash
PYTHONPATH=/mnt/data/lpwan_audit/bundled_simpy:. python -m pytest -q
```

On a clean local installation after installing `requirements.txt`, run `python -m pytest -q` without the audit-host `PYTHONPATH` override.

**Final result:** `25 passed in 0.93s` (0 failed, 0 skipped) on the final rerun.

Test breakdown:

| Test file | Tests | Coverage |
|---|---:|---|
| `tests/test_suite.py` | 10 | AHP reciprocity/CR, synthetic criterion trade-offs, TOPSIS tie behaviour, modem state transitions, energy accounting, 5G outage registration/recovery, fallback/reselection |
| `tests/test_math_engine_standalone.py` | 7 | AHP/TOPSIS numeric validation and candidate handling |
| `tests/test_audit_statistics_standalone.py` | 3 | Benjamini-Hochberg implementation |
| `tests/test_paired_statistics.py` | 5 | Valid paired inference, identical zero differences, constant non-zero differences, non-finite inputs/insufficient pairs, alpha validation |
| **Total** | **25** | |

The new paired-statistics tests ensure that zero-variance paired differences do not receive a fabricated p-value, t-based confidence interval, or standardized effect size.

## Compilation

**Command:**

```bash
python -m compileall -q src experiments tests
```

**Result:** completed successfully; no Python syntax errors.

## Simulation smoke test

**Command:**

```bash
python experiments/run_experiments.py smoke
```

**Result:** one `A_NORMAL` smoke configuration completed with all six strategies (6 records). The smoke output is written to `results/raw/smoke_test_metrics.csv`; the archived primary raw data are not overwritten. This is a smoke test, not the full primary experiment.

## Primary-data audit and figure generation

**Commands:**

```bash
python experiments/audit_existing_results.py
python experiments/generate_figures.py
```

**Results:**
- Primary archive integrity assertions passed: 4,320 rows, 24 configurations, 30 seeds, six strategies, zero duplicate primary keys.
- Selection-analysis assertions passed: 2,880 unique rows and 5,768,175 AHP ranking invocations.
- The 60 `Emerg_Lat_s` missing values were verified to occur only where `Emerg_PDR = 0`.
- The audit regenerated `results/processed/paired_stats.csv`, the paired-statistics/FDR diagnostics, candidate-input and dominance tables, and `docs/EXPERIMENTS_AND_REPRODUCIBILITY.md`.
- The figure generator completed and generated eight figures (seven primary figures plus one separate 5G-outage pilot figure).

## Clean supplementary 5G-outage pilot reproduction

A clean working clone was made and all five per-seed checkpoints were removed before simulation. The simulator executed five seeds × six strategies = **30 simulations**. The first summary pass exposed a missing import for the new paired-statistics helper; the import was corrected, and the summary/validation stage then completed using those freshly generated checkpoints.

Verified against the packaged prior pilot:
- All five `seed_1000.csv` … `seed_1004.csv` files matched exactly as data frames.
- `raw_metrics.csv` matched exactly (30 × 21).
- `selection_summary.csv` matched exactly (6 × 5).
- Aggregate means and raw event/selection counts remain unchanged.
- `summary.csv` was intentionally corrected: confidence-interval bounds are now blank where the across-seed sample standard deviation is zero, instead of reporting a zero-width t interval.
- `paired_vs_fixed5g.csv` retains the paired-t results and adds Shapiro-Wilk and Wilcoxon signed-rank sensitivity fields. The Wilcoxon BH-FDR family contains five strategy comparisons per metric; none of the five-seed pilot Wilcoxon q-values is below 0.05.

The 30 pilot records remain separate from the 4,320 primary rows.

## Not performed / not claimed

- The complete 24 × 30 × 6 primary SimPy experiment was **not rerun**. The archived 4,320-row primary matrix was validated and retained.
- No native Windows execution was performed in this Linux audit environment. The Windows PowerShell instructions are provided, but a fresh Windows virtual environment test on the submission computer remains pending.
- No physical LoRaWAN gateway, modem, cellular network, RF propagation, EPC/5GC hardware, or 6G tests were performed.
- The five-seed outage pilot is a small functional validation and is not a basis for broad statistical generalization.

---

## Application update validation

# Application Update Validation

## Update
Added the **Our modifications & performance impact** research page to the LPWAN Edge Intelligence app. It consolidates:

- Existing technologies and methods versus the team's implemented design choices.
- A selected 2021–2025 related-work comparison with DOI links.
- The fixed-NB-IoT reference versus adaptive AHP-TOPSIS measured baseline table.
- The fixed-5G control and the explicit no-AHP-only-gain caveat.
- Cause-and-effect explanations for QoS filtering, candidate dominance, state-dependent weights and modem wake/setup energy.
- Energy and decision-computation overhead.
- The separate five-seed outage/recovery pilot.
- The logical framework-design status and future-work boundaries.

## Validation performed

- `node --check frontend/app.js` — passed.
- `node --check frontend/simulation-engine.js` — passed.
- `node --test tests/*.test.cjs` — 19 passed, 0 failed, 0 skipped.
- `python verify_project.py` — passed; validated 4,320 primary rows, 24 scenarios, 30 seeds, six algorithms, 30 separate outage rows and compilation of 13 bundled Python source files.
- Local HTTP server — root page, JS, CSS, JSON and data assets served successfully with `curl`.

A headless Chromium visual run could not be completed in this environment because the browser runtime rejected local HTTP navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. The page-generation route and content were tested through the Node integration tests. Please open the local app in Chrome/Edge on Windows for the final interactive visual check.

## Important boundaries retained

- “Before” means the fixed-NB-IoT simulation reference, not a physical pre-deployment result.
- Fixed 5G is a control and has identical primary baseline metrics to adaptive AHP-TOPSIS.
- The 5G outage pilot remains separate from the primary matrix.
- Predictive energy, hysteresis and predictive availability are future work, not implemented features.

---

## Application build and validation

# Build and validation record

## Architecture

- `frontend/`: self-contained HTML, CSS and JavaScript application. No npm packages, CDN, external font or remote chart dependency is required.
- `frontend/simulation-engine.js`: shared browser-side state, feasibility, AHP weight, TOPSIS and selector logic.
- `frontend/data/`: derived JSON index, source CSV copies, supplementary pilot records and original project figure assets.
- `../simulation/`: single canonical Python/SimPy source tree and experiment/data files.
- `backend/api.py`: optional FastAPI bridge. It imports the canonical `EdgeGateway` and algorithm implementations and runs fresh simulations in memory without writing archived CSV results.

## Tests run in the build environment

- `node --check frontend/app.js` — passed.
- `node --check frontend/simulation-engine.js` — passed.
- `node --test tests/engine.test.cjs` — 15 passed, 0 failed, 0 skipped.
- `python verify_project.py` — passed; confirms the 4,320-row primary dataset, 24 scenarios, 30 seeds, six algorithms, separate 30-row outage pilot, source-file presence and Python source compilation.
- `python -m py_compile backend/api.py backend/run_api.py run_app.py` — passed.
- Local HTTP fetch checks for index, CSS, JS, JSON, logo and the 1.67 MB primary CSV — HTTP 200.

## Not verified in this environment

- The optional FastAPI/SimPy bridge was not executed end-to-end because SimPy is not installed in this build environment. Install `backend/requirements.txt` to enable it.
- The full page was not successfully captured in a headless-browser screenshot in this environment. Static resource serving, JavaScript syntax, engine tests and dataset integrity were checked.
- No primary 4,320-run experiment was rerun as part of building this application.

## Data boundary

The archived primary experiment and separate outage pilot are immutable recorded research datasets. Browser-demo outputs are generated independently and are not merged into those records. Fresh API simulations are also independent and are not appended to archived results.

---

## Build notes

# Build and validation notes — final audited revision

## Source changes retained from the prepared revision

- `src/core/math_engine.py`: finite/positive/reciprocal matrix checks, a Saaty Random Index table, principal-eigenvalue consistency calculation, normalized-weight validation and deterministic tie handling were added while preserving the four design weight vectors.
- `src/core/algorithms.py`: state weights are cached to avoid recomputing the same AHP matrix for every packet.
- `src/simulation/network.py`: a 5G availability-outage event was added to exercise the existing availability/QoS feasibility filter. It does not add a new radio protocol or handover implementation.
- `tests/test_suite.py`: two tests were added for the 5G outage event and fallback/recovery behaviour.
- `experiments/run_5g_outage_supplementary.py`: a five-seed, six-strategy supplementary outage pilot was added, with output isolated from the 24-configuration primary matrix.
- `src/core/paired_statistics.py`: added a shared paired-inference helper that leaves t statistics, p-values, t confidence intervals and Cohen’s dz undefined for zero-variance paired differences rather than assigning p = 1.0. Added five tests for valid, zero-variance, constant-nonzero, insufficient and invalid inputs.
- `experiments/audit_existing_results.py`: deterministic AHP, Pareto/input and paired-statistics diagnostic tables were added; it now regenerates 144 paired-stat rows and separate Wilcoxon/Shapiro/BH-FDR diagnostics from the archived raw primary file.
- `experiments/generate_figures.py`: the supplementary figure now reads `results/supplementary/5g_outage/raw_metrics.csv`, not the primary raw CSV. This fixes a source-path mismatch that previously meant the pilot figure depended on a scenario that is intentionally absent from the 24-configuration matrix.

## Independent validation in this audit

- Python 3.13.5; NumPy 2.3.5; Pandas 2.2.3; SciPy 1.17.0; Matplotlib 3.10.8; pytest 9.0.2.
- SimPy 4.1.2 was supplied from the original archive as pure-Python source because SimPy was not installed in the host environment and package-network access was unavailable.
- `PYTHONPATH=/mnt/data/lpwan_audit/bundled_simpy python -m pytest -q`: **25 passed**.
- `PYTHONPATH=/mnt/data/lpwan_audit/bundled_simpy:/mnt/data/LPWAN_FINAL_WORK python experiments/run_experiments.py smoke`: six algorithms completed for one smoke configuration; primary files were not changed.
- `python experiments/audit_existing_results.py`: generated the audit diagnostics from the archived primary CSVs.
- `PYTHONPATH=/mnt/data/lpwan_audit/bundled_simpy python experiments/run_5g_outage_supplementary.py --seeds 5`: 30 runs completed after removing pilot checkpoints in a separate working copy; `seed_1000.csv` through `seed_1004.csv`, `raw_metrics.csv` (30 × 21) and `selection_summary.csv` (6 × 5) matched the packaged pilot data exactly. `summary.csv` was intentionally corrected so zero-SD confidence intervals are undefined; `paired_vs_fixed5g.csv` was extended with Shapiro-Wilk and Wilcoxon sensitivity fields, so those derived files are not byte-identical to the older summaries.
- `python experiments/generate_figures.py`: generated seven primary figures and one separate supplementary pilot figure.
- Final audit suite: **25 passed, 0 failed, 0 skipped**. `python -m compileall -q src experiments tests` succeeded.

## Important execution boundary

The full 4,320-run primary experiment was not rerun. Its supplied dataset was audited for row counts, uniqueness, missingness, key coverage and energy-accounting consistency. The original archive was preserved unchanged. The supplied Windows `.venv` is not portable to this Linux host; the validation used the host Python plus the original archive's pure-Python SimPy source.


## Final repository reorganisation checks (17 November 2026)

The following checks were freshly run against the reorganised paths in this release:

- `node --check frontend/app.js` — passed.
- `node --check frontend/simulation-engine.js` — passed.
- `node --test tests/*.test.cjs` — **19 passed, 0 failed**.
- `python verify_project.py` — passed; primary CSV has 4,320 unique records, 24 scenarios, 30 seeds and six strategies; separate outage pilot has 30 rows; 13 Python source files compile.
- `python -m compileall -q src experiments tests` — passed.
- Three Python test modules that do not require SimPy — **15 passed**.
- Local HTTP resource checks — root page, CSS, JavaScript, logo, app JSON and the 4,320-row primary CSV all returned HTTP 200.

The full SimPy-dependent Python suite was **not freshly rerun in this build environment**: SimPy was not installed and the environment could not access the package index. The earlier project validation record reports 25 Python tests passed, and the user previously reported successful local Windows execution. After extracting this reorganised bundle, run the full Python suite locally using the commands in the root README.

The full 4,320-run primary experiment was not rerun during packaging. The archived primary results were preserved.
