# Submission reproducibility and execution guide

## Project layout

- `Framework/` — canonical Python/SimPy research implementation, experiments, tests, raw/processed results and supplementary outputs.
- `Simulation/` — browser research dashboard, optional FastAPI bridge to the canonical Framework code, browser tests and local launch scripts.
- `docs/` — maintained architecture, research, results, reproducibility and demonstration documentation. See [`docs/README.md`](../README.md) for the index.
- `deliverables/` — final project report, student research-paper draft and presentation, each with an editable source and rendered PDF.

## Python environment (Windows PowerShell)

```powershell
cd Framework
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m pytest tests -q
py experiments/audit_backhaul_extensibility.py
```

The primary 4,320-row experiment is preserved and does not need to be rerun to reproduce the report. The completed TSC 900-trace results are included as raw and processed outputs. Re-running the 900-trace matrix is optional and will take several minutes; use the documented `--max-runtime-s` guard.

## Optional browser dashboard

```powershell
cd Simulation
py -3.13 run_app.py
```

Open `http://127.0.0.1:8000`. The browser-only lab is an interactive approximation, not a canonical SimPy run.

## Optional SimPy bridge

In a second terminal:

```powershell
cd Simulation
py -3.13 -m pip install -r backend/requirements.txt
py -3.13 backend/run_api.py
```

The API uses canonical Python modules under `../Framework/`; fresh runs are independent and are not appended to archived datasets.

## Browser and project checks

```powershell
cd Simulation
node --check frontend/app.js
node --check frontend/simulation-engine.js
node --test tests/*.test.cjs
py -3.13 verify_project.py
```

## Important provenance rules

- Do not merge primary, outage-pilot, targeted TSC and 900-trace matrix outputs. They are different experiment families.
- The primary 4,320-row matrix is historical; it was audited, not rerun for the TSC extension.
- The TSC 900-trace matrix pairs the exact same generated input trace for AHP-TOPSIS and TSC within each seed/condition.
- Browser-demo outputs are not research results.
- Analytical operating-region outputs are not SimPy outcomes.
- The 6G profile is exploratory/non-selectable; no 6G performance values exist.

## Suggested professor demonstration

1. Explain the original fixed-NB-IoT reference and the two simulated cellular backhaul choices.
2. Show the original feasibility → gateway state → AHP → TOPSIS pipeline.
3. Explain why the original adaptive AHP selected 5G throughout the primary matrix.
4. Demonstrate the TSC session preference, emergency packet override and outage fallback.
5. Show the 900-trace condition matrix and only the condition-wise statistically supported results.
6. Discuss energy boundary, no PDR/emergency-PDR gain, no switching reduction and no full 6G.
7. Close with modem-lifecycle calibration, predictive queue control and variable-link validation as future work.

## Final submission deliverables

- `deliverables/FINAL_PROJECT_REPORT.pdf` and `.docx` — complete project report (PDF + editable source).
- `deliverables/RESEARCH_PAPER_DRAFT.pdf` and `.docx` — student research-paper draft (PDF + editable source).
- `deliverables/FINAL_PROJECT_PRESENTATION.pdf` and `.pptx` — professor presentation (PDF + editable slides).
- `docs/demo/DEMO_AND_VIVA_GUIDE.md` — suggested demonstration flow and likely technical questions.
- `docs/reproducibility/SUBMISSION_CHECKLIST.md` — final department/team review checklist.
