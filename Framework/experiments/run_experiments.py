import os
import simpy
import numpy as np
import pandas as pd
from scipy import stats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.simulation.network import EdgeGateway
from src.core.algorithms import FixedNB, Fixed5G, LatFirst, EnerFirst, StatTOP, AdapAHP
from src.core.paired_statistics import paired_t_summary

def generate_trace(seed, rate, dur, emerg_ratio):
    np.random.seed(seed)
    t, tr, pid = 0, [], 0
    while t < dur:
        t += np.random.exponential(1.0/rate)
        if t > dur: break
        e = np.random.rand() < emerg_ratio
        tr.append({
            'pid': pid, 'arr': t, 'emerg': e, 
            'payload': 200 if e else 50, 
            'rel_roll': {'NB': np.random.rand()*100, '5G': np.random.rand()*100}
        })
        pid += 1
    return tr

def generate_events(scen):
    evs = []
    if scen == "E_LAT_DEGRADE": evs.append({'type': 'E_LAT_DEGRADE', 'start': 1000, 'dur': 60})
    if scen == "F_OUTAGE": evs.append({'type': 'NB_OUTAGE', 'start': 2000, 'dur': 30})
    return evs

def check_pareto_dominance(df):
    """Vectorized per-packet Pareto comparison; same four criteria as original."""
    out = df.copy()
    out["pareto_status"] = "NONE_FEASIBLE"
    nb = out["feas_nb"].fillna(False).to_numpy(dtype=bool)
    g5 = out["feas_5g"].fillna(False).to_numpy(dtype=bool)
    both = nb & g5
    single = nb ^ g5

    nb_better = np.zeros(len(out), dtype=np.int8)
    g5_better = np.zeros(len(out), dtype=np.int8)
    # Lower is better for latency/energy; higher is better for reliability/bandwidth.
    comparisons = [
        ("lat_nb_pred", "lat_5g_pred", True),
        ("eng_nb_pred", "eng_5g_pred", True),
        ("rel_nb", "rel_5g", False),
        ("bw_nb", "bw_5g", False),
    ]
    for left, right, lower_is_better in comparisons:
        a = out[left].to_numpy()
        b = out[right].to_numpy()
        if lower_is_better:
            nb_better += both & (a < b)
            g5_better += both & (b < a)
        else:
            nb_better += both & (a > b)
            g5_better += both & (b > a)

    status = np.full(len(out), "NONE_FEASIBLE", dtype=object)
    status[single] = "SINGLE_FEASIBLE"
    status[both & (nb_better > 0) & (g5_better == 0)] = "NB_DOM"
    status[both & (g5_better > 0) & (nb_better == 0)] = "5G_DOM"
    status[both & ~(((nb_better > 0) & (g5_better == 0)) | ((g5_better > 0) & (nb_better == 0)))] = "NO_DOM"
    out["pareto_status"] = status
    return out

def run_all(smoke_test=False):
    res_dir = Path(__file__).resolve().parent.parent / "results"
    (res_dir / "raw").mkdir(parents=True, exist_ok=True)
    (res_dir / "processed").mkdir(parents=True, exist_ok=True)
    raw_checkpoint = res_dir / "raw" / "raw_paired_metrics.csv"
    selection_checkpoint = res_dir / "processed" / "selection_analysis.csv"
    # Full runs resume from completed (Scenario, Algorithm, Seed) rows. Smoke runs stay isolated.
    completed = set()
    had_full_checkpoint = (not smoke_test) and raw_checkpoint.exists()
    if not smoke_test and not had_full_checkpoint and selection_checkpoint.exists():
        # Discard the earlier smoke-test selection file; it is not a full-run checkpoint.
        selection_checkpoint.unlink()
    if not smoke_test and raw_checkpoint.exists():
        try:
            prior = pd.read_csv(raw_checkpoint)
            required = {"Scenario", "Algorithm", "Seed"}
            if required.issubset(prior.columns):
                completed = set(zip(prior["Scenario"], prior["Algorithm"], prior["Seed"].astype(int)))
            else:
                raise ValueError("checkpoint lacks required key columns")
        except Exception as exc:
            raise RuntimeError(f"Cannot safely resume from {raw_checkpoint}: {exc}") from exc
    print(f"Resume: {len(completed)} of 4320 simulation runs already checkpointed.", flush=True)

    algos = {"NB": FixedNB(), "5G": Fixed5G(), "LAT": LatFirst(), "ENG": EnerFirst(), "TOP": StatTOP(), "AHP": AdapAHP()}

    # EXACTLY 24 CONFIGURATIONS
    scenarios = [
        ("A_NORMAL", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("B_EMERG", 2.0, 0.50, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("C_LOWBATT", 2.0, 0.10, 19.0, 5.0, 1.0, 1.0, 1.0),
        ("D_CONFLICT", 2.0, 0.50, 19.0, 5.0, 1.0, 1.0, 1.0),
        ("E_LAT_DEGRADE", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("F_OUTAGE", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("G_LOAD_0.5", 0.5, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("G_LOAD_1.0", 1.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("G_LOAD_2.0", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("G_LOAD_4.0", 4.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("G_LOAD_8.0", 8.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("H_ENG_BASE", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("H_ENG_NB_NEG50", 2.0, 0.10, 100.0, 5.0, 1.0, 0.5, 1.0),
        ("H_ENG_NB_POS50", 2.0, 0.10, 100.0, 5.0, 1.0, 1.5, 1.0),
        ("H_ENG_5G_NEG50", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 0.5),
        ("H_ENG_5G_POS50", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.5),
        ("I_REL_BASELINE", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("I_REL_NB_1", 2.0, 0.10, 100.0, 1.0, 1.0, 1.0, 1.0),
        ("I_REL_NB_5", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("I_REL_NB_10", 2.0, 0.10, 100.0, 10.0, 1.0, 1.0, 1.0),
        ("I_REL_5G_1", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0),
        ("I_REL_5G_5", 2.0, 0.10, 100.0, 5.0, 5.0, 1.0, 1.0),
        ("I_REL_5G_10", 2.0, 0.10, 100.0, 5.0, 10.0, 1.0, 1.0),
        ("J_OVERHEAD", 2.0, 0.10, 100.0, 5.0, 1.0, 1.0, 1.0)
    ]

    seeds = [1000] if smoke_test else list(range(1000, 1030))
    if smoke_test: scenarios = [scenarios[0]]

    data = []
    sel_analysis = []
    valid_terminals = {"DELIVERED", "DROP_QOS", "DROP_OUTAGE", "DROP_RELIABILITY", "DROP_QUEUE_OVERFLOW_CPU", "DROP_QUEUE_OVERFLOW_BH"}

    for scen_name, rate, eratio, batt, l_nb, l_5g, nb_e_scale, g5_e_scale in scenarios:
        print(f"Running {scen_name}...", flush=True)
        for seed_index, seed in enumerate(seeds, start=1):
            tr_base = generate_trace(seed, rate, 3600, eratio)
            ev_base = generate_events(scen_name)

            for algo_index, (name, algo) in enumerate(algos.items(), start=1):
                if (scen_name, name, int(seed)) in completed:
                    continue
                print(f"  {scen_name} | seed {seed_index}/{len(seeds)} ({seed}) | {name} ({algo_index}/6)", flush=True)
                env = simpy.Environment()
                tr_copy = [dict(p) for p in tr_base]
                gw = EdgeGateway(env, algo, tr_copy, ev_base)

                gw.a1.rel = 100.0 - l_nb
                gw.a2.rel = 100.0 - l_5g

                gw.a1.set_energy *= nb_e_scale; gw.a1.tx_pow *= nb_e_scale
                gw.a2.set_energy *= g5_e_scale; gw.a2.tx_pow *= g5_e_scale

                gw.battery_j = (batt/100.0) * gw.max_batt
                env.run(until=3600)
                gw.end_of_simulation_sweep()

                df = pd.DataFrame(list(gw.registry.values()))

                # STRICT PACKET ACCOUNTING ASSERTION
                n_gen = len(df)
                n_del = len(df[df['status'] == "DELIVERED"])
                n_drop = len(df[df['status'].isin(valid_terminals) & (df['status'] != "DELIVERED")])
                n_flight = len(df[df['status'].str.startswith("IN_FLIGHT_")])
                assert n_gen == (n_del + n_drop + n_flight), f"Leak: Gen({n_gen}) != Del({n_del}) + Drop({n_drop}) + Flight({n_flight})"

                df = check_pareto_dominance(df)

                deliv = df[df['status'] == "DELIVERED"]
                emerg = deliv[deliv['emerg'] == True]
                emerg_tot = df[df['emerg'] == True]

                nb_util = (gw.a1.total_tx_time / 3600) * 100
                g5_util = (gw.a2.total_tx_time / 3600) * 100

                nb_sel = len(df[df.get('sel_net', -1) == 0])
                g5_sel = len(df[df.get('sel_net', -1) == 1])

                data.append({
                    "Scenario": scen_name,
                    "Algorithm": name,
                    "Seed": seed,
                    "Generated": n_gen,
                    "PDR": n_del / n_gen if n_gen else 0,
                    "Emerg_PDR": len(emerg) / len(emerg_tot) if len(emerg_tot) else 0,
                    "Avg_Lat_s": deliv['lat_actual'].mean() if len(deliv) else float('nan'),
                    "Med_Lat_s": deliv['lat_actual'].median() if len(deliv) else float('nan'),
                    "95th_Lat_s": deliv['lat_actual'].quantile(0.95) if len(deliv) else float('nan'),
                    "Emerg_Lat_s": emerg['lat_actual'].mean() if len(emerg) else float('nan'),
                    "Throughput_bps": (deliv['payload'].sum() * 8) / 3600.0,
                    "NB_Util_Pct": nb_util, "5G_Util_Pct": g5_util,
                    "NB_Sel": nb_sel,
                    "5G_Sel": g5_sel,
                    "Switches": gw.switches,
                    "Avg_CPU_Q_Len": gw.cpu_q_area / 3600,
                    "Avg_NB_Q_Len": gw.a1.q_area / 3600,
                    "Avg_5G_Q_Len": gw.a2.q_area / 3600,
                    "CPU_Q_Delay_s": df['cpu_q_delay'].dropna().mean(),
                    "BH_Q_Delay_s": df['bh_q_delay'].dropna().mean(),
                    "Algo_Time_Max_us": df['algo_time_us'].dropna().max(),
                    "Algo_Time_Mean_us": df['algo_time_us'].dropna().mean(),
                    "CPU_Eng_J": gw.cpu_energy_consumed,
                    "NB_Setup_Tx_Eng_J": gw.a1.energy_setup_tx_j,
                    "5G_Setup_Tx_Eng_J": gw.a2.energy_setup_tx_j,
                    "Total_Eng_J": gw.cpu_energy_consumed + gw.a1.energy_setup_tx_j + gw.a2.energy_setup_tx_j,
                    "QoS_Violations_Deliv": len(deliv[deliv['lat_actual'] > np.where(deliv['emerg'], 1.0, 10.0)]),
                    "QoS_Drop": len(df[df['status'] == "DROP_QOS"]),
                    "Outage_Drop": len(df[df['status'] == "DROP_OUTAGE"])
                })

                # Selection Analysis Export (AHP only)
                if name == "AHP":
                    for st in ["NORMAL", "EMERGENCY", "LOW_BATTERY", "CONFLICT"]:
                        st_df = df[df.get('ahp_state', '') == st]
                        sel_analysis.append({
                            "Scenario": scen_name, "Seed": seed, "AHP_State": st,
                            "Total_Decisions": len(st_df),
                            "NB_Sel": len(st_df[st_df.get('sel_net', -1) == 0]),
                            "5G_Sel": len(st_df[st_df.get('sel_net', -1) == 1]),
                            "Dom_NB": len(st_df[st_df['pareto_status'] == "NB_DOM"]),
                            "Dom_5G": len(st_df[st_df['pareto_status'] == "5G_DOM"]),
                            "Dom_None": len(st_df[st_df['pareto_status'] == "NO_DOM"]),
                            "Single_Feas": len(st_df[st_df['pareto_status'] == "SINGLE_FEASIBLE"]),
                            "NB_Sel_Pct": (len(st_df[st_df.get('sel_net', -1) == 0]) / len(st_df) * 100) if len(st_df) else 0.0,
                            "5G_Sel_Pct": (len(st_df[st_df.get('sel_net', -1) == 1]) / len(st_df) * 100) if len(st_df) else 0.0
                        })

                # Durable checkpoint after every completed algorithm/seed simulation.
                if not smoke_test:
                    pd.DataFrame([data[-1]]).to_csv(raw_checkpoint, mode="a", header=not raw_checkpoint.exists(), index=False)
                    if name == "AHP":
                        pd.DataFrame(sel_analysis[-4:]).to_csv(selection_checkpoint, mode="a", header=not selection_checkpoint.exists(), index=False)

    if smoke_test:
        res = pd.DataFrame(data)
    else:
        res = pd.read_csv(raw_checkpoint) if raw_checkpoint.exists() else pd.DataFrame(data)
        # Rebuild selection analysis from its durable checkpoint.
        if selection_checkpoint.exists():
            sel_df = pd.read_csv(selection_checkpoint)
        else:
            sel_df = pd.DataFrame(sel_analysis)
        sel_df.to_csv(selection_checkpoint, index=False)

    expected_rows = 1 * 1 * 6 if smoke_test else 24 * 30 * 6
    assert len(res) == expected_rows, f"Matrix incomplete! Expected {expected_rows}, got {len(res)}"
    if not smoke_test:
        assert not res.duplicated(subset=["Scenario", "Algorithm", "Seed"]).any(), "Duplicate checkpoint keys detected."
        assert res.groupby("Scenario").size().eq(180).all(), "Each scenario must contain 30 seeds x 6 algorithms."
    # Seed Validation
    assert set(res['Seed']) == set(seeds), "Seed coverage mismatch in output matrix."

    if smoke_test:
        res.to_csv(res_dir / "raw" / "smoke_test_metrics.csv", index=False)
        return True

    # PAIRED T-TEST STATISTICS
    summary_rows = []
    for scen in res['Scenario'].unique():
        scen_data = res[res['Scenario'] == scen]
        ahp_data = scen_data[scen_data['Algorithm'] == 'AHP'].copy()

        for algo in res['Algorithm'].unique():
            algo_data = scen_data[scen_data['Algorithm'] == algo].copy()

            # Merge explicitly by Scenario & Seed enforcing ONE-TO-ONE
            merged = pd.merge(algo_data, ahp_data, on=['Scenario', 'Seed'], suffixes=('_algo', '_ahp'), validate="one_to_one")
            assert len(merged) == len(algo_data), "Missing or duplicate seeds in paired merge."

            metrics = ['PDR', 'Avg_Lat_s', 'Total_Eng_J']
            stats_dict = {"Scenario": scen, "Algorithm": algo}

            for m in metrics:
                algo_m = f"{m}_algo"
                ahp_m = f"{m}_ahp"

                clean_algo = pd.to_numeric(merged[algo_m], errors="coerce").dropna()
                mean_summary = paired_t_summary(clean_algo.to_numpy(dtype=float), alpha=0.05)
                mean_val = float(clean_algo.mean()) if not clean_algo.empty else float('nan')

                stats_dict[f"{m}_Mean"] = mean_val
                stats_dict[f"{m}_CI"] = mean_summary["CI_Half_Width"]

                if algo != 'AHP':
                    differences = (
                        pd.to_numeric(merged[algo_m], errors="coerce")
                        - pd.to_numeric(merged[ahp_m], errors="coerce")
                    )
                    comparison = paired_t_summary(differences.to_numpy(dtype=float), alpha=0.05)
                else:
                    comparison = {
                        "Valid_Pairs": int(merged[algo_m].notna().sum()),
                        "Mean_Difference": 0.0,
                        "CI_Half_Width": float('nan'),
                        "T_Statistic": float('nan'),
                        "P_Value": float('nan'),
                        "Shapiro_W": float('nan'),
                        "Shapiro_P": float('nan'),
                        "Wilcoxon_P_Value": float('nan'),
                        "Wilcoxon_Method": "Self-comparison not tested",
                        "Inference_Status": "SELF_COMPARISON_NOT_TESTED",
                    }

                stats_dict[f"{m}_Valid_Pairs"] = comparison["Valid_Pairs"]
                stats_dict[f"{m}_Diff_vs_AHP"] = comparison["Mean_Difference"]
                stats_dict[f"{m}_Diff_CI"] = comparison["CI_Half_Width"]
                stats_dict[f"{m}_T_Stat"] = comparison["T_Statistic"]
                stats_dict[f"{m}_P_Value"] = comparison["P_Value"]
                stats_dict[f"{m}_Shapiro_W"] = comparison["Shapiro_W"]
                stats_dict[f"{m}_Shapiro_P"] = comparison["Shapiro_P"]
                stats_dict[f"{m}_Wilcoxon_P_Value"] = comparison["Wilcoxon_P_Value"]
                stats_dict[f"{m}_Inference_Status"] = comparison["Inference_Status"]

            summary_rows.append(stats_dict)

    sum_df = pd.DataFrame(summary_rows)
    assert len(sum_df) == 144, f"Summary Matrix incomplete! Expected 144, got {len(sum_df)}"
    sum_df.to_csv(res_dir / "processed" / "paired_stats.csv", index=False)
    print("Completed: 4320 raw rows and 144 paired-statistics rows.", flush=True)

if __name__ == "__main__":
    import sys
    run_all(smoke_test="smoke" in sys.argv)
