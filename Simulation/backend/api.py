"""Optional FastAPI bridge for the canonical sibling Framework Python/SimPy model.
It writes no files and never mutates archived experiment CSVs.
"""
from __future__ import annotations
import sys, time
from dataclasses import replace
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT = REPO_ROOT / "Framework"
REQUIRED_FRAMEWORK_FILES = (
    PROJECT / "src/core/algorithms.py",
    PROJECT / "src/core/math_engine.py",
    PROJECT / "src/core/paired_statistics.py",
    PROJECT / "src/core/two_timescale.py",
    PROJECT / "src/core/two_timescale_config.json",
    PROJECT / "src/simulation/network.py",
)
sys.path.insert(0, str(PROJECT))

def framework_missing_files() -> list[str]:
    return [str(path.relative_to(PROJECT)) for path in REQUIRED_FRAMEWORK_FILES if not path.is_file()]

app = FastAPI(title="LPWAN Edge Intelligence · SimPy Bridge", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(127\.0\.0\.1|localhost):[0-9]+", allow_methods=["GET", "POST"], allow_headers=["*"])

class RunRequest(BaseModel):
    algorithm: Literal["NB", "5G", "LAT", "ENG", "TOP", "AHP", "TSC"] = "AHP"
    arrival_rate_pps: float = Field(2.0, ge=0.1, le=8.0)
    emergency_ratio: float = Field(0.1, ge=0.0, le=0.6)
    battery_pct: float = Field(100.0, ge=0.0, le=100.0)
    seed: int = Field(2026, ge=0, le=2147483647)
    duration_s: int = Field(600, ge=10, le=3600)
    nb_available: bool = True
    fiveg_available: bool = True
    nb_reliability_pct: float = Field(95.0, ge=0, le=100)
    fiveg_reliability_pct: float = Field(99.0, ge=0, le=100)
    nb_energy_scale: float = Field(1.0, ge=0.1, le=5.0)
    fiveg_energy_scale: float = Field(1.0, ge=0.1, le=5.0)
    event: Literal["none", "nb_outage", "5g_outage", "5g_latency_degrade"] = "none"
    event_start_s: int = Field(100, ge=0, le=3500)
    event_duration_s: int = Field(30, ge=1, le=600)

@app.get('/api/health')
def health():
    dependency_error = None
    versions = {}
    try:
        import simpy, numpy, pandas
        versions = {"simpy": simpy.__version__, "numpy": numpy.__version__, "pandas": pandas.__version__}
    except Exception as exc:
        dependency_error = str(exc)
    missing = framework_missing_files()
    framework_ok = not missing
    dependencies_ok = dependency_error is None
    return {
        "ok": dependencies_ok and framework_ok,
        "dependencies_ok": dependencies_ok,
        "framework_available": framework_ok,
        "framework_root": str(PROJECT),
        "missing_framework_files": missing,
        "dependency_error": dependency_error,
        **versions,
        "source": "canonical sibling Framework/src",
        "detail": None if dependencies_ok and framework_ok else (
            f"Missing Framework source files: {', '.join(missing)}" if missing
            else f"SimPy backend dependencies unavailable: {dependency_error}"
        ),
    }

@app.post('/api/simpy/run')
def run_simpy(req: RunRequest):
    missing = framework_missing_files()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=("The optional SimPy bridge needs the full project Framework folder beside Simulation. "
                    f"Missing: {', '.join(missing)}"),
        )
    try:
        import simpy
        import numpy as np
        import pandas as pd
        from src.simulation.network import EdgeGateway
        from src.core.algorithms import FixedNB, Fixed5G, LatFirst, EnerFirst, StatTOP, AdapAHP, TwoTimescale
        from src.core.two_timescale import load_two_timescale_config
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Install backend/requirements.txt to enable the original SimPy bridge: {exc}")
    algos = {"NB": FixedNB, "5G": Fixed5G, "LAT": LatFirst, "ENG": EnerFirst, "TOP": StatTOP, "AHP": AdapAHP}
    algo = (lambda: TwoTimescale(replace(load_two_timescale_config(), initial_arrival_rate_pps=req.arrival_rate_pps))) if req.algorithm == "TSC" else algos[req.algorithm]
    np.random.seed(req.seed)
    t, trace, pid = 0.0, [], 0
    while t < req.duration_s:
        t += float(np.random.exponential(1.0 / req.arrival_rate_pps))
        if t > req.duration_s:
            break
        emergency = bool(np.random.rand() < req.emergency_ratio)
        trace.append({"pid": pid, "arr": t, "emerg": emergency, "payload": 200 if emergency else 50,
                      "rel_roll": {"NB": float(np.random.rand() * 100), "5G": float(np.random.rand() * 100)}})
        pid += 1
    if not trace:
        raise HTTPException(status_code=422, detail="The requested run produced no packets; increase duration or arrival rate.")
    events = []
    evmap = {"nb_outage": "NB_OUTAGE", "5g_outage": "5G_OUTAGE", "5g_latency_degrade": "E_LAT_DEGRADE"}
    if req.event != "none":
        if req.event_start_s + req.event_duration_s > req.duration_s:
            raise HTTPException(status_code=422, detail="The event must finish within the simulation duration.")
        events = [{"type": evmap[req.event], "start": req.event_start_s, "dur": req.event_duration_s}]
    env = simpy.Environment()
    gw = EdgeGateway(env, algo(), trace, events)
    gw.a1.rel, gw.a2.rel = req.nb_reliability_pct, req.fiveg_reliability_pct
    gw.a1.set_energy *= req.nb_energy_scale; gw.a1.tx_pow *= req.nb_energy_scale
    gw.a2.set_energy *= req.fiveg_energy_scale; gw.a2.tx_pow *= req.fiveg_energy_scale
    gw.a1.avail, gw.a2.avail = req.nb_available, req.fiveg_available
    gw.battery_j = req.battery_pct / 100.0 * gw.max_batt
    start = time.perf_counter()
    try:
        env.run(until=req.duration_s)
        gw.end_of_simulation_sweep()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Original SimPy model failed: {exc}")
    wall = time.perf_counter() - start
    df = pd.DataFrame(list(gw.registry.values()))
    statuses = df["status"].astype(str)
    delivered = df[statuses == "DELIVERED"]
    emergency_total = df[df["emerg"].astype(bool)]
    emergency_delivered = delivered[delivered["emerg"].astype(bool)]
    total = len(df)
    metrics = {
        "generated": total,
        "delivered": int(len(delivered)),
        "PDR": float(len(delivered) / total) if total else 0.0,
        "mean_latency_s": float(delivered["lat_actual"].mean()) if len(delivered) else None,
        "p95_latency_s": float(delivered["lat_actual"].quantile(.95)) if len(delivered) else None,
        "emergency_generated": int(len(emergency_total)),
        "emergency_delivered": int(len(emergency_delivered)),
        "emergency_PDR": float(len(emergency_delivered) / len(emergency_total)) if len(emergency_total) else None,
        "qos_drops": int((statuses == "DROP_QOS").sum()),
        "outage_drops": int((statuses == "DROP_OUTAGE").sum()),
        "reliability_drops": int((statuses == "DROP_RELIABILITY").sum()),
        "cpu_queue_drops": int((statuses == "DROP_QUEUE_OVERFLOW_CPU").sum()),
        "backhaul_queue_drops": int((statuses == "DROP_QUEUE_OVERFLOW_BH").sum()),
        "nb_selections": int((df.get("sel_net", pd.Series(index=df.index, dtype=float)) == 0).sum()),
        "fiveg_selections": int((df.get("sel_net", pd.Series(index=df.index, dtype=float)) == 1).sum()),
        "switches": int(gw.switches),
        "cpu_energy_j": float(gw.cpu_energy_consumed),
        "nb_energy_j": float(gw.a1.energy_setup_tx_j),
        "fiveg_energy_j": float(gw.a2.energy_setup_tx_j),
        "total_energy_j": float(gw.cpu_energy_consumed + gw.a1.energy_setup_tx_j + gw.a2.energy_setup_tx_j),
        "controller_diagnostics": ({
            "persistent_switches": gw.algo.controller.persistent_switches,
            "packet_qos_overrides": gw.algo.controller.packet_overrides,
            "forced_fallbacks": gw.algo.controller.forced_fallbacks,
            "session_index": gw.algo.controller.session_index,
        } if hasattr(gw.algo, "controller") else None),
        "mean_algorithm_time_us": float(df["algo_time_us"].dropna().mean()) if df["algo_time_us"].notna().any() else None,
        "battery_remaining_pct": float(gw.battery_j / gw.max_batt * 100),
    }
    return {"ok": True, "mode": "fresh-original-simpy", "algorithm": req.algorithm, "seed": req.seed,
            "duration_s": req.duration_s, "wall_time_s": wall, "metrics": metrics,
            "note": "Fresh independent run using bundled source. Not merged into archived research data."}
