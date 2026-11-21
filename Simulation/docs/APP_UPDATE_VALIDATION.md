# Application Update Validation — 1.2.0

## Update scope

This repair restores and hardens the existing project dashboard without changing the research model, archived data, strategy definitions, experiment parameters or project scope.

Changes:

- Restored the missing command-centre overview renderer required by the default `overview` route.
- Restored the Viva question bank referenced by the Viva page.
- Removed a broken topology image path; the existing in-app SVG is the single topology visual.
- Added explicit dataset schema/count checks before dashboard rendering.
- Separated data-fetch errors from JavaScript rendering errors so a render exception is no longer reported as a failed JSON download.
- Added a retry control, readable startup diagnostics and a data-ready status label.
- Added local HTTP health check, configurable port, no-cache response headers and port-conflict diagnostics.
- Corrected the optional SimPy bridge status reporting to check required sibling Framework modules.
- Corrected validation/documentation for the actual `Simulation/` + sibling `Framework/` layout.

## Evidence and boundaries retained

- The primary 4,320-row experiment remains immutable recorded data.
- The five-seed 5G outage pilot remains separate.
- The TSC 900-trace matrix remains separate from the primary baseline matrix.
- Browser-demo metrics remain illustrative and are not new SimPy experiment results.
- Fixed 5G and adaptive AHP-TOPSIS remain identical in the primary baseline metrics; no adaptive superiority over fixed 5G is claimed.
- IMT-2030/6G remains a non-selectable exploratory profile; no 6G radio/core or performance result is claimed.

## Local checks

Run from this folder:

```bash
node --check frontend/app.js
node --check frontend/simulation-engine.js
node --test tests/*.test.cjs
python verify_project.py
```

The optional SimPy API check is only executable when the sibling Framework and packages in `backend/requirements.txt` are available. Use `http://127.0.0.1:8001/api/health` to confirm the bridge prerequisites.


Automated verification result for this archive: **32 Node tests passed, 0 failed**. Python compilation and `verify_project.py` also passed. The optional SimPy bridge was not end-to-end executed because this upload contains Simulation/ without the sibling Framework/ source.
