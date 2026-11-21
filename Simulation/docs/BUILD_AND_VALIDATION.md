# Build and validation record

## Architecture

- `frontend/`: self-contained HTML, CSS and JavaScript application. No npm packages, CDN, external font or remote chart dependency is required.
- `frontend/simulation-engine.js`: shared browser-side state, feasibility, AHP weight, TOPSIS and selector logic.
- `frontend/app.js`: dashboard navigation, recorded-data views, browser lab, export actions and startup validation.
- `frontend/data/`: derived JSON index, source CSV copies, supplementary pilot records and original project figure assets.
- `backend/api.py`: optional FastAPI bridge. It imports the canonical Python/SimPy code from the sibling `../Framework/` folder and runs fresh simulations in memory without writing archived CSV results.
- `run_app.py`: local static HTTP server with configurable port, no-cache headers and `/healthz` check.

The original Framework source is deliberately not duplicated inside this Simulation folder. The full project keeps `Framework/` and `Simulation/` as sibling directories. The browser dashboard and archived research panels do not depend on the optional API.

## Defects corrected in application update 1.2.0

- Restored the missing `renderOverview()` landing-page renderer. Previously the JSON fetch could succeed, but the initial `render()` call failed because the default page renderer was undefined; the shared promise catch then incorrectly displayed “Data failed to load”.
- Restored the missing `QAS` data used by Viva mode.
- Removed a topology image reference to `../docs/figures/unified_backhaul_architecture.png`, which is not present in the uploaded Simulation archive. The page uses its existing generated SVG topology instead.
- Separated JSON loading/validation errors from dashboard rendering errors and added a retry action.
- Added dataset shape and primary-count validation before rendering.
- Added cache-busting response headers so an old browser cache does not keep an earlier app bundle or JSON dataset after an update.
- Added a local `/healthz` endpoint and a clear port-in-use message.
- Made the optional API health check validate the sibling Framework files as well as Python dependencies.
- Updated the tests and validator so a Simulation-only extraction can validate the browser dashboard without falsely reporting that the separate optional Framework dependency is bundled.

## Validation performed for this build

- `node --check frontend/app.js` — passed.
- `node --check frontend/simulation-engine.js` — passed.
- `node --test tests/*.test.cjs` — 32 passed, 0 failed; see `tests/TEST_RESULTS.txt`.
- `python verify_project.py` — validates bundled research data and frontend assets. It checks the sibling Framework source when present and reports the bridge as optional when absent.
- Dashboard render smoke test — all 11 page renderers executed using the bundled JSON data; startup was also tested for both successful data loading and a simulated request failure.
- Browser simulation smoke test — 1,000 seeded packets processed by the browser engine without a JavaScript exception.
- Local HTTP smoke test — root page, app JS, CSS, dataset, primary CSV, logo and `/healthz` served successfully; port-conflict diagnostics were exercised.
- Visual limitation — a full interactive Chrome visual pass on the user’s Windows machine was not performed in this build environment. The user should open the replacement build locally for final visual inspection.

## Scope not claimed as validated

- The optional FastAPI/SimPy bridge requires the full sibling Framework source and installed dependencies. A Simulation-only ZIP does not contain that source, so the API cannot execute a fresh original-model run without the rest of the project.
- No primary research experiment was rerun as part of the dashboard repair.
- The archived baseline, outage and TSC research datasets were retained as supplied; the dashboard repair does not modify those experimental results.
