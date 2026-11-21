# LPWAN Edge Intelligence — Simulation Dashboard

Interactive browser dashboard for the IIIT Raichur Computer Networks project. This application is self-contained for the recorded research views and the browser demonstration. The optional Python/SimPy bridge uses the canonical `Framework/` source directory from the full project.

## 1. Start the browser dashboard (Windows)

1. Extract the project ZIP.
2. Keep the `Simulation` and `Framework` folders beside each other in the full project directory. The browser dashboard itself only needs `Simulation/`.
3. Open the `Simulation` folder.
4. Double-click `start_windows.bat`, or open PowerShell in this folder and run:

```powershell
py -3.13 run_app.py
```

Open **http://127.0.0.1:8000** in Chrome or Edge. Keep the terminal open while using the dashboard. Stop it with `Ctrl+C`.

The server health endpoint is **http://127.0.0.1:8000/healthz**. It confirms that the HTML, JavaScript and bundled JSON dataset are present.

Do not open `frontend/index.html` directly. The dashboard fetches the JSON dataset and source CSV files over HTTP; direct `file://` access is not supported.

### If port 8000 is already in use

Close the earlier dashboard terminal or start this copy on another port:

```powershell
py -3.13 run_app.py --port 8010
```

Then open **http://127.0.0.1:8010**. Only one server can use a port at a time.

## 2. Dashboard modes

1. **Recorded research mode** reads the static copies of the primary 4,320-row dataset, derived summaries and separate supplementary outputs. These are archived results, not regenerated when the page opens.
2. **Browser demonstration mode** runs a seeded, simplified client-side packet/decision model. Its metrics are illustrative and are not new SimPy experiment results.
3. **Optional SimPy bridge** starts an independent fresh simulation through FastAPI using canonical Python modules in the sibling `../Framework/` folder. Fresh runs are never appended to archived research datasets.

## 3. Optional Python/SimPy API

This mode requires the complete project folder layout, with `Framework/` beside `Simulation/`. It is not enabled by extracting this `Simulation` directory by itself.

In a second PowerShell window:

```powershell
cd Simulation
py -3.13 -m pip install -r backend/requirements.txt
py -3.13 backend/run_api.py
```

The API listens on **http://127.0.0.1:8001**. Check **http://127.0.0.1:8001/api/health** before clicking either SimPy run button in the dashboard. The health response checks both the Python packages and required `Framework/src` source files. A missing Framework folder is reported as an unavailable optional bridge; it does not prevent the browser dashboard or recorded data panels from working.

## 4. Research panels and data provenance

The dashboard explains the original six-strategy primary experiment and the separate Two-Timescale Controller (TSC) paired matrix. The canonical TSC matrix is under:

`../Framework/results/supplementary/two_timescale/multi_operating_point/`

It contains 30 conditions, 900 paired traces and 1,800 algorithm-run metric records. The dashboard uses compact derived summaries, not the full decision log.

Important distinctions:

- Primary 4,320-row experiment: historical baseline, audited and not rerun for the TSC extension.
- 5G outage pilot: separate five-seed supplement.
- TSC 30-seed smoke validation: separate targeted integration check.
- TSC 900-trace matrix: 30 operating conditions × 30 paired seeds.
- Analytical operating-region sweep: parameter analysis, not a SimPy network experiment.
- Browser-only lab: demonstration approximation, not archived research evidence.

## 5. Validation

From the `Simulation` folder (Node.js 18+ and Python 3.10+):

```powershell
node --check frontend/app.js
node --check frontend/simulation-engine.js
node --test tests/*.test.cjs
py -3.13 verify_project.py
```

When the full project is available, also run from the project root:

```powershell
py -3.13 -m pytest Framework/tests -q
py -3.13 Framework/experiments/audit_backhaul_extensibility.py
```

The Simulation validator checks the dashboard assets, research JSON, primary CSV integrity, and Python source compilation when the sibling Framework directory is present. In a standalone Simulation-only extraction, it reports the optional Framework dependency without failing the browser-dashboard validation.

## 6. Backhaul profile maturity

| Profile | Status | Selectable? |
|---|---|---:|
| NB-IoT | Implemented simulated adapter | Yes |
| 5G NR | Implemented simulated adapter | Yes |
| IMT-2030/6G | Exploratory capability/profile template with no numeric radio metrics | No |

No 6G radio interface, core, protocol or performance experiment is included. The profile contract is an architectural extension point only.

## 7. Model boundaries

- Logical topology and simplified candidate service/energy profiles.
- No physical LoRaWAN PHY/MAC, airtime/collision model, modem, operator core or field validation.
- No full LTE EPC/5G Core, N3IWF or standardised ATSSS.
- TSC accounts for configured setup-cost amortisation but does not include calibrated modem idle-tail/sleep leakage or nonzero switching energy.
- No statistical PDR/emergency-PDR improvement or switching reduction is established by the 900-trace matrix.
