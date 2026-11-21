from __future__ import annotations

import csv
import json
import py_compile
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
FRONT = APP_ROOT / "frontend"
FRAMEWORK = REPO_ROOT / "Framework"
errors: list[str] = []
warnings: list[str] = []

# Validate the bundled application data and its declared experiment structure.
data_path = FRONT / "data" / "app-data.json"
try:
    data = json.loads(data_path.read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"app-data.json: {exc}")
    data = {}

required_sections = {
    "source", "algorithm_order", "algorithms", "weights", "backhauls", "gateway",
    "baseline", "load_sweep", "reliability_sensitivity", "overhead", "outage_summary",
    "scenario_meta", "scenario_results", "limitations", "tsc_matrix",
}
if data:
    missing = sorted(required_sections - data.keys())
    if missing:
        errors.append(f"app-data.json missing sections: {', '.join(missing)}")
    source = data.get("source", {})
    if source.get("primary_rows") != 4320:
        errors.append(f"JSON primary_rows {source.get('primary_rows')} != 4320")
    if source.get("supplementary_outage_rows") != 30:
        errors.append("JSON supplementary outage row count mismatch")
    if len(data.get("baseline", [])) != 6:
        errors.append("JSON baseline must contain six strategies")
    if len(data.get("scenario_meta", [])) != 24:
        errors.append("JSON scenario metadata must contain 24 scenarios")
    if data.get("tsc_matrix", {}).get("paired_traces") != 900:
        errors.append("JSON TSC matrix must declare 900 paired traces")

# Validate the raw primary matrix: exact row count, dimensions and unique keys.
raw = FRONT / "data" / "primary_results" / "raw_paired_metrics.csv"
rows = []
try:
    with raw.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    keys = {(row["Scenario"], row["Algorithm"], row["Seed"]) for row in rows}
    if len(rows) != 4320:
        errors.append(f"primary CSV rows {len(rows)} != 4320")
    if len(keys) != len(rows):
        errors.append("primary CSV contains duplicate scenario/algorithm/seed keys")
    if len({row["Scenario"] for row in rows}) != 24:
        errors.append("primary CSV scenario count mismatch")
    if len({row["Seed"] for row in rows}) != 30:
        errors.append("primary CSV seed count mismatch")
    if len({row["Algorithm"] for row in rows}) != 6:
        errors.append("primary CSV algorithm count mismatch")
except Exception as exc:
    errors.append(f"primary CSV: {exc}")

# Ensure browser resources and referenced data exports are shipped together.
frontend_required = [
    "index.html", "app.css", "app.js", "simulation-engine.js",
    "assets/iiit-raichur-logo.png", "data/app-data.json",
]
for relative in frontend_required:
    if not (FRONT / relative).is_file():
        errors.append(f"missing frontend asset: {relative}")

app_source = (FRONT / "app.js").read_text(encoding="utf-8") if (FRONT / "app.js").is_file() else ""
for relative in [
    "data/primary_results/raw_paired_metrics.csv",
    "data/primary_results/paired_stats.csv",
    "data/primary_results/selection_analysis.csv",
]:
    if relative in app_source and not (FRONT / relative).is_file():
        errors.append(f"missing referenced data export: {relative}")
if "../docs/figures/unified_backhaul_architecture.png" in app_source:
    errors.append("topology page still references an external image that is not part of Simulation")
if "function renderOverview(" not in app_source:
    errors.append("default command-centre renderer is missing")
if "const QAS = [" not in app_source:
    errors.append("Viva question bank is missing")

# The SimPy bridge intentionally uses the original project Framework as a sibling.
# It is optional for the browser dashboard and therefore is not a Simulation ZIP error.
required_framework = [
    "src/core/algorithms.py",
    "src/core/math_engine.py",
    "src/core/paired_statistics.py",
    "src/core/two_timescale.py",
    "src/core/two_timescale_config.json",
    "src/simulation/network.py",
]
framework_file_count = 0
if FRAMEWORK.is_dir():
    for relative in required_framework:
        if not (FRAMEWORK / relative).is_file():
            errors.append(f"missing required sibling Framework source: {relative}")
    for source_file in FRAMEWORK.rglob("*.py"):
        framework_file_count += 1
        try:
            py_compile.compile(str(source_file), doraise=True)
        except Exception as exc:
            errors.append(f"Framework Python compile {source_file.relative_to(FRAMEWORK)}: {exc}")
else:
    warnings.append("Sibling Framework/ folder is not present. Browser dashboard is self-contained; optional SimPy API cannot run from this Simulation-only extraction.")

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("VALIDATION PASSED")
print(
    f"Primary rows: {len(rows)} | scenarios: 24 | seeds: 30 | algorithms: 6 | "
    f"supplementary outage rows: {data['source']['supplementary_outage_rows']}"
)
print("Frontend JSON, HTML/CSS/JS assets and project data exports: present")
if FRAMEWORK.is_dir():
    print(f"Sibling Framework Python source files compiled: {framework_file_count}")
else:
    print("Optional SimPy bridge: not runnable without sibling Framework/ and backend requirements")
for warning in warnings:
    print(f"NOTE: {warning}")
