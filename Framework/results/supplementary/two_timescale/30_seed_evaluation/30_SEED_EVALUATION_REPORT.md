# 30-Seed Paired Evaluation — Two-Timescale Backhaul Controller

**Simulation horizon:** 120.0 s per seed  
**Offered load:** 2.0 packets/s  
**Emergency traffic:** 10%  
**Seeds:** 30 (1000–1029)  
**Outage:** 40–60 s  
**Wall runtime recorded by runner:** 4.080 s

> **Evidence classification:** targeted paired simulation evaluation (exploratory). It is not the original 3,600-second baseline experiment and does not establish performance across all traffic loads or outage patterns.

## 1. Aggregate outcome

| Metric | Existing AHP-TOPSIS | Two-timescale |
|---|---:|---:|
| Generated packets | 7,051 | 7,051 |
| Delivered packets | 6,828 | 6,837 |
| Pooled PDR | 96.8373% | 96.9650% |
| Emergency PDR | 85.6938% | 85.6938% |
| Total modelled energy | 205.1257 J | 205.3273 J |
| Energy / delivered packet | 0.03004184 J | 0.03003178 J |
| QoS drops | 92 | 92 |
| Outage drops | 2 | 2 |
| Reliability drops | 128 | 119 |
| Mean decision time (mean across seeds) | 269.36 µs | 42.93 µs |

The pooled PDR difference is **+0.1276 percentage points**. Mean latency decreases by **0.0537 s** when comparing per-seed means; mean P95 decreases by **0.1518 s**. Total modelled energy changes by **+0.098%**. Mean measured selector time decreases by **84.06%** in this runtime environment.

## 2. Paired statistical analysis

The unit of analysis is the paired seed (n=30). Two-sided Wilcoxon signed-rank tests compare per-seed metrics. Holm-Bonferroni correction is applied across the six reported endpoints. The 95% confidence interval is a paired t-interval for the mean within-seed difference (proposed minus baseline). These are exploratory tests because the run is one traffic load, one horizon and one outage schedule.

| Endpoint | Mean paired difference (TSC − AHP) | 95% paired t CI | Raw Wilcoxon p | Holm-adjusted p | Seeds better / tied / worse |
|---|---:|---:|---:|---:|---:|
| Packet delivery ratio | +0.00124108 fraction | [7.54099e-05, 0.00240674] | 0.04252 | 0.1276 | 6 / 23 / 1 |
| Mean end-to-end latency | -0.0536546 seconds | [-0.094219, -0.0130902] | 0.0009815 | 0.004908 | 14 / 16 / 0 |
| P95 end-to-end latency | -0.151812 seconds | [-0.267098, -0.0365263] | 0.003346 | 0.01338 | 11 / 19 / 0 |
| Emergency packet delivery ratio | +0 fraction | [0, 0] | 1 | 1 | 0 / 30 / 0 |
| Total modelled energy | +0.00671947 joules | [-0.0377426, 0.0511816] | 0.1093 | 0.2187 | 12 / 16 / 2 |
| Mean decision computation time | -226.429 microseconds | [-246.297, -206.561] | 1.863e-09 | 1.118e-08 | 30 / 0 / 0 |

**Interpretation:** mean latency, P95 latency and decision computation time remain statistically different after the six-endpoint Holm correction in this targeted experiment. PDR has a small positive raw paired difference, but it does **not** survive Holm correction. Emergency PDR is identical. Total modelled energy has no statistically supported difference. Statistical significance for selector computation time does not imply end-to-end network performance superiority.

## 3. Controller decision evidence

- Recorded TSC decisions: 6,959.
- Decision modes: `{"emergency_fastest_feasible": 588, "forced_feasibility_fallback": 30, "packet_qos_override": 19, "session_hold": 6135, "session_reoptimization": 32, "session_start": 155}`.
- Persistent controller switch events: 62.
- Packet-level QoS overrides: 19.
- Forced fallbacks: 30.
- During the configured outage, 1,078 recorded decisions selected NB-IoT only: True.
- After outage recovery, the controller selected 5G in 96.33% of recorded packet decisions.

The outage scenario demonstrates functional fallback and recovery. It does not prove better outage performance than AHP-TOPSIS: both methods had two packet-level network changes per seed on average, and the two-timescale method had 62 persistent switch events compared with 60 baseline packet-selection changes. The experiment therefore does not demonstrate reduced switching in this particular outage trace.

## 4. What the results support

**Supported for this targeted configuration**
- The two-timescale controller executed in SimPy over 30 paired input traces.
- It produced a slightly higher pooled PDR (+9 delivered packets across 7,051 generated), driven by nine fewer reliability drops; the emergency PDR did not change.
- It produced lower per-seed mean and P95 latency in a subset of runs and was never worse on these two latency averages in this dataset (ties are common).
- It used less selector computation time in all 30 paired runs.
- It performed fallback to NB-IoT for all decisions recorded during the 5G outage window and reselected 5G after recovery in most post-outage decisions.

**Not established**
- Lower total energy: total modelled energy was slightly higher (+0.098%) and the difference is not statistically significant.
- Better emergency PDR: identical between methods (599/699 delivered).
- Reduced handover/switching: not demonstrated in this experiment.
- General superiority across loads, session patterns, longer horizons or multiple outage patterns.
- Real modem energy efficiency or hardware battery lifetime.

## 5. Model and experiment limitations

1. The evaluation uses one offered load (2 packets/s), a 120-second horizon, 10% emergency traffic and one 20-second 5G outage.
2. Idle-tail power and switching energy are configured as zero because the source simulator does not provide calibrated values; modelled energy includes CPU, setup and transmission components.
3. The expected burst size uses a Poisson gap-cluster approximation and an EWMA arrival-rate estimate; it is not a learned or measured traffic forecast.
4. Latency feasibility uses deterministic predicted delay; no probabilistic deadline guarantee is modelled.
5. AHP-TOPSIS and the new controller share the same underlying simplified modem and network abstractions. This is not a physical NB-IoT/5G deployment.
6. The decision-time comparison is software timing in one execution environment, not a hardware-independent complexity proof.
7. P-values are exploratory. The small PDR effect is not significant after multiple-endpoint correction.

## 6. Reproduction

From `Framework/`:
```powershell
py -3.13 -m pip install -r requirements.txt
py -3.13 experiments/run_two_timescale_smoke.py --duration-s 120 --rate-pps 2 --emergency-ratio 0.10 --seeds 1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029 --outage-start-s 40 --outage-duration-s 20
py -3.13 experiments/analyze_two_timescale_results.py
```

The first command reproduces the dependency setup; the second reruns the targeted 30-seed evaluation and overwrites only the targeted output CSVs in this supplementary folder; the third generates statistical summaries and figures. Historical primary results are not touched.

## 7. Generated figures

- `pdr_paired_scatter.png`
- `mean_latency_paired_scatter.png`
- `p95_latency_paired_scatter.png`
- `energy_paired_scatter.png`
- `decision_time_paired_scatter.png`
- `backhaul_selection_share.png`
- `outage_selection_timeline.png`
