# Experiments and Reproducibility

This consolidated reference combines the experiment/data audit, reproducibility diagnostics and execution guide. It documents the archived primary matrix separately from supplementary analyses and the outage pilot. Unless otherwise stated, paths such as `results/`, `experiments/` and `src/` below are relative to the repository's `simulation/` directory.

---

## Experiment and data audit

# Experiment and Data Audit Report

**Audit date:** 14 November 2026  
**Project:** Unifying 5G/6G with LPWAN — gateway-centric adaptive backhaul selection

## 1. Primary experiment matrix and integrity

The archived primary experiment was retained without rerunning the full 4,320 simulations.

| Item | Verified count |
|---|---:|
| Configurations | 24 |
| Paired seeds | 30 (1000–1029) |
| Strategies | 6 |
| Raw metric rows | 4,320 |
| Paired-statistics rows | 144 |
| Selection-analysis rows | 2,880 |
| AHP ranking invocations | 5,768,175 |
| Duplicate `(Scenario, Algorithm, Seed)` keys | 0 |
| Duplicate `(Scenario, Seed, AHP_State)` keys | 0 |

Each primary scenario has 180 raw rows (30 seeds × six strategies). The selection-analysis file has 2,880 unique scenario/seed/state rows.

The simulator's total energy column is consistent with the component sum:

\[
E_{total}=E_{CPU}+E_{NB,setup+tx}+E_{5G,setup+tx}.
\]

The maximum absolute floating-point residual across the primary matrix is approximately \(1.14\times10^{-13}\) J.

## 2. Baseline comparison

Means over the 30 archived seeds in `A_NORMAL`:

| Strategy | PDR | Mean latency | 95th-percentile latency | Emergency PDR | Total energy |
|---|---:|---:|---:|---:|---:|
| Fixed NB-IoT | 86.83% | 2.8689 s | 7.3506 s | 16.88% | 129.29 J |
| Fixed 5G | 99.02% | 0.02743 s | 0.03052 s | 99.10% | 135.24 J |
| Adaptive AHP-TOPSIS | 99.02% | 0.02743 s | 0.03052 s | 99.10% | 135.24 J |

Adaptive AHP-TOPSIS selected 5G in every recorded primary ranking invocation. Therefore, in this baseline parameterization, it matches fixed 5G and does not demonstrate an adaptive switching or performance advantage in the primary matrix.

## 3. Candidate-input values and criterion directions

The values below are derived from the implementation's candidate model at initial modem sleep; they are not physical measurements. The packet payload/deadline pairs are 50 B / 10 s for telemetry and 200 B / 1 s for emergency traffic.

| State | Candidate | Predicted latency (s; minimize) | Marginal energy (J; minimize) | Configured reliability (%; maximize) | Nominal bandwidth (bps; maximize) | Initial-sleep QoS feasible |
|---|---|---:|---:|---:|---:|---|
| NORMAL / LOW_BATTERY | NB-IoT | 2.006061 | 1.506061 | 95 | 66,000 | Yes |
| NORMAL / LOW_BATTERY | 5G NR | 0.120004 | 0.500012 | 99 | 100,000,000 | Yes |
| EMERGENCY / CONFLICT | NB-IoT | 2.024242 | 1.524242 | 95 | 66,000 | No |
| EMERGENCY / CONFLICT | 5G NR | 0.120016 | 0.500048 | 99 | 100,000,000 | Yes |

The implementation derives the candidate values as follows:

- Predicted latency = setup delay + base latency + packet serialization time.
- Initial-sleep marginal energy = setup energy + transmit power × packet serialization time.
- Feasibility requires the predicted latency to be no greater than the packet deadline.

The normal and low-battery rows share the same representative packet/model inputs; their AHP preferences differ. The emergency and conflict rows also share their packet/model inputs, but use different state-dependent preference weights. The table explains why 5G is strongly favoured by the current initial-sleep model. The marginal-energy value is not a forecast of full-horizon modem energy and does not include future wake-up cycles, queue evolution, CPU processing, or sleep/tail leakage.

## 4. Pareto-dominance method and denominator

The four criteria are:
- Latency: minimize.
- Candidate gateway backhaul energy estimate: minimize.
- Configured reliability: maximize.
- Nominal bandwidth: maximize.

For calls in which both alternatives pass the hard availability/QoS feasibility filter, candidate X Pareto-dominates Y if X is no worse on all four criteria and strictly better on at least one. The two-feasible calls are partitioned into 5G-dominates, NB-IoT-dominates, or neither-dominates. Calls where exactly one alternative is feasible are counted separately and are not pairwise Pareto comparisons.

| Mutually exclusive outcome | Decisions | % of all AHP ranking calls | % of both-feasible calls |
|---|---:|---:|---:|
| 5G dominates NB-IoT | 4,827,117 | 83.69% | 96.13% |
| NB-IoT dominates 5G | 0 | 0.00% | 0.00% |
| Neither dominates | 194,210 | 3.37% | 3.87% |
| Only one candidate feasible | 746,848 | 12.95% | N/A |
| **Total** | **5,768,175** | **100.00%** | |

The all-calls denominator is 5,768,175 actual AHP ranking invocations. Packets for which neither candidate is feasible are rejected before ranking and therefore are not counted as AHP invocations. Both-feasible calls total 5,021,327. Thus the 83.69% dominance share is 96.13% when conditioned on both candidates being feasible. Percentages are calculated from unrounded counts; displayed values can differ by 0.01 percentage point due to rounding.

`NO_DOM` does not mean equal candidates: each alternative is better on at least one criterion. TOPSIS still selected 5G in those calls. The data do not support a statement that 5G Pareto-dominates every individual decision.

## 5. Undefined emergency-latency aggregates

The primary raw file contains 60 missing `Emerg_Lat_s` values. All 60 occur where `Emerg_PDR = 0`, in the NB-IoT strategy for `G_LOAD_4.0` and `G_LOAD_8.0` (30 rows per scenario).

The simulator defines emergency latency as the mean latency of successfully delivered emergency packets. When no emergency packet is delivered, the mean has no observations and is undefined. It is not zero latency, because zero would imply a delivered packet with a measured zero delay. It is not a missing simulation run: the simulation record, generated traffic, and emergency delivery ratio remain present. The values are retained as NaN, not imputed as zero.

## 6. Paired statistical protocol

For each scenario and each non-AHP strategy, differences are calculated on matching seeds as:

\[
d_i = x_{i,algorithm}-x_{i,AHP}.
\]

The primary inferential test is a two-sided paired Student t-test, implemented as a one-sample t-test of the paired differences against zero. Its assumptions include independent seed replicates and an approximately normal distribution of paired differences. The 95% confidence interval is t-based. Paired Cohen's \(d_z\) is the mean paired difference divided by the sample standard deviation of the paired differences.

The analysis inventory contains 120 non-AHP comparisons per metric (five non-AHP strategies × 24 scenarios). Recalculation from the archived raw seeds gives:

| Metric | Comparison records | Estimable paired t-tests | Exact zero-difference comparisons (not tested) | Shapiro-Wilk p < 0.05 |
|---|---:|---:|---:|---:|
| PDR | 120 | 24 | 96 | 2 |
| Mean latency | 120 | 24 | 96 | 0 |
| Total energy | 120 | 24 | 96 | 1 |

For 96 comparisons per metric, the paired difference vector is identically zero. Those rows are descriptive identity comparisons: their mean difference and observed range are zero, but the sample variance is zero, so a Student-t statistic, p-value, t-based confidence interval, and Cohen's \(d_z\) are non-estimable. The updated code stores NaN for inferential fields; it does **not** convert them to p = 1.0. Constant non-zero difference vectors are treated similarly. The canonical 144-row `paired_stats.csv` retains all six strategies; the AHP-versus-AHP self-comparison is explicitly marked `SELF_COMPARISON_NOT_TESTED`.

For the 24 estimable paired-t comparisons per metric, Shapiro-Wilk is an exploratory normality diagnostic, not proof of the assumption. It falls below 0.05 for 2 of 24 PDR comparisons, 1 of 24 energy comparisons, and none of the mean-latency comparisons. A two-sided Wilcoxon signed-rank test (zero paired differences omitted; SciPy `method=auto`) is included as a non-parametric sensitivity analysis. For the primary matrix, all 24 estimable Wilcoxon comparisons in each metric family remain below 0.05 after Benjamini-Hochberg adjustment.

Benjamini-Hochberg false-discovery-rate adjustment is performed separately per metric for paired-t p-values and separately per metric for Wilcoxon sensitivity p-values. Non-estimable comparisons are excluded from the relevant FDR family rather than assigned artificial p-values. In this dataset, the FDR family size is 24 estimable values per metric for each method. The additional `results/tables/paired_statistics_bh_fdr.csv` records the p-values, q-values, effect sizes, confidence intervals, Shapiro diagnostics, Wilcoxon sensitivity results, and inference status.

## 7. AHP matrix consistency

The four state pairwise comparison matrices are formed directly as ratios of design-specified weight vectors. They are reciprocal and yield \(\lambda_{max}=4\), CI approximately zero, and CR approximately zero (with a negligible floating-point residual for EMERGENCY). This confirms internal mathematical consistency by construction; it does not validate the selected preferences through expert elicitation.

## 8. Separate supplementary 5G outage/recovery pilot

The supplementary 5G outage pilot is independent of the primary 24-configuration matrix. It uses five seeds (1000–1004), six strategies, 3,600 s per run, and a 5G availability outage from 2,000 s to 2,030 s, producing 30 records.

The five per-seed simulation files and the 30-row `raw_metrics.csv` were regenerated in a clean clone and matched the previously supplied records exactly. The adaptive AHP-TOPSIS pilot means over five seeds are:

| Metric | Mean |
|---|---:|
| PDR | 98.935% |
| Emergency PDR | 98.434% |
| Mean latency | 0.05361 s |
| Total simulated energy | 138.97 J |
| NB-IoT selections during outage window | 57.2 |
| 5G selections during outage window | 0 |
| 5G selections after recovery | 3,098.2 |
| Selected-backhaul label changes | 2.0 per seed |
| QoS drops | 4.8 per seed |
| Outage drops | 0 per seed |

Fixed 5G PDR in the same pilot is 98.193%. Adaptive AHP-TOPSIS makes eligible NB-IoT selections while 5G is unavailable and returns to 5G after recovery. These are selected-backhaul label changes, not 3GPP mobility handovers. The five-seed sample is a functional pilot, not broad inferential evidence.

The refreshed pilot summary now reports blank confidence-interval bounds for across-seed statistics with zero sample variance rather than presenting a zero-width interval. Its `paired_vs_fixed5g.csv` adds Shapiro-Wilk and Wilcoxon sensitivity results. With five strategy comparisons per metric, none of the pilot's Wilcoxon BH-adjusted q-values is below 0.05; the pilot is not used for broad statistical claims.

All supplementary files remain under `results/supplementary/5g_outage/` and are not appended to the primary raw CSV.

## 9. Energy-model interpretation

Cumulative simulation energy is:

\[
E_{total}=E_{CPU}+E_{NB,setup+tx}+E_{5G,setup+tx}.
\]

The selector's candidate energy is an instantaneous marginal estimate for the current packet and modem state; it is not a horizon-aware estimate of future wake/sleep costs. The cumulative simulator records modem setup and packet transmission energy plus gateway CPU processing; sleep and idle-tail leakage are excluded.

In the seed-1000 baseline diagnostic, NB-IoT has 10 modem wake/setup cycles while 5G has 141. The faster 5G service returns to sleep more often under the configured tail timer, resulting in repeated setup events. Across 30 baseline seeds, mean total energy is 129.29 J for fixed NB-IoT and 135.24 J for fixed 5G/adaptive AHP-TOPSIS. This is specific to the simulator's model and parameters, not a universal real-world technology comparison. A horizon-aware estimator should only be implemented after calibrating expected traffic and modem-state transition costs; no such estimator was introduced in this revision.

## 10. Reproducibility boundary

- The primary 4,320-row raw matrix was audited but the full 4,320-run primary simulation was not rerun.
- The 30-run supplementary 5G outage pilot was freshly executed in a clean clone and its seed-level/raw data were verified.
- The paired-statistics diagnostics, 144-row paired summary, and eight figures were regenerated.
- The 800-case decision-sensitivity script remains a separate synthetic offline analysis; it is not a network simulation or physical measurement.
- No native Windows run or physical hardware test was performed in this audit environment.

---

## Reproducible project diagnostics

# Reproducible Project Diagnostics

This report is generated from the archived CSV outputs and the current analysis code. It does not rerun the primary SimPy simulations.

## Primary Archive Integrity

The primary archive contains 4,320 rows across 24 configurations, 30 seeds, and 6 strategies. The (Scenario, Algorithm, Seed) key has 0 duplicates. The separate selection-analysis archive contains 2,880 unique rows and 5,768,175 ranking invocations.

`Emerg_Lat_s` is undefined in 60 rows. All these rows have `Emerg_PDR = 0`: the simulation generated emergency traffic but delivered no emergency packets for that aggregate, so no delivered-emergency latency mean exists. This is not a zero-latency measurement and is not a missing simulation row. The undefined values are preserved rather than imputed as zero.

## AHP Consistency

| Scenario | Algorithm | Generated | PDR | Emerg_PDR | Avg_Lat_s | Med_Lat_s | 95th_Lat_s | Emerg_Lat_s | Throughput_bps | NB_Util_Pct | 5G_Util_Pct | NB_Sel | 5G_Sel | Switches | Avg_CPU_Q_Len | Avg_NB_Q_Len | Avg_5G_Q_Len | CPU_Q_Delay_s | BH_Q_Delay_s | Algo_Time_Max_us | Algo_Time_Mean_us | CPU_Eng_J | NB_Setup_Tx_Eng_J | 5G_Setup_Tx_Eng_J | Total_Eng_J | QoS_Violations_Deliv | QoS_Drop | Outage_Drop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J_OVERHEAD | AHP | 7155 | 0.991474 | 0.994382 | 0.027753 | 0.025004 | 0.032731 | 0.026935 | 1024.222222 | 0.000000 | 0.001032 | 0 | 7155 | 0 | 0.000048 | 0.000000 | 0.005394 | 0.000024 | 0.002714 | 10346.700030 | 523.426569 | 71.550000 | 0.000000 | 70.611492 | 142.161492 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7170 | 0.992190 | 0.992647 | 0.027714 | 0.025004 | 0.031839 | 0.027226 | 1015.444444 | 0.000000 | 0.001023 | 0 | 7170 | 0 | 0.000049 | 0.000000 | 0.005318 | 0.000025 | 0.002670 | 2614.800003 | 507.952831 | 71.700000 | 0.000000 | 72.610520 | 144.310520 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7266 | 0.990917 | 0.994100 | 0.027220 | 0.025004 | 0.028399 | 0.026573 | 1024.666667 | 0.000000 | 0.001033 | 0 | 7266 | 0 | 0.000046 | 0.000000 | 0.004432 | 0.000023 | 0.002196 | 8976.800018 | 516.867204 | 72.660000 | 0.000000 | 59.611600 | 132.271600 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7183 | 0.988863 | 0.990182 | 0.027351 | 0.025004 | 0.031160 | 0.027422 | 1024.555556 | 0.000000 | 0.001036 | 0 | 7183 | 0 | 0.000063 | 0.000000 | 0.004591 | 0.000031 | 0.002301 | 2901.000029 | 507.703425 | 71.830000 | 0.000000 | 60.111864 | 131.941864 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7193 | 0.989017 | 0.986053 | 0.027365 | 0.025004 | 0.029462 | 0.027101 | 1026.111111 | 0.000000 | 0.001038 | 0 | 7193 | 0 | 0.000042 | 0.000000 | 0.004633 | 0.000021 | 0.002319 | 6177.700008 | 515.891061 | 71.930000 | 0.000000 | 61.112128 | 133.042128 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7023 | 0.990033 | 0.995542 | 0.027456 | 0.025004 | 0.030557 | 0.028024 | 995.888889 | 0.000000 | 0.001005 | 0 | 7023 | 0 | 0.000044 | 0.000000 | 0.004729 | 0.000023 | 0.002424 | 3937.700007 | 507.804001 | 70.230000 | 0.000000 | 67.108504 | 137.338504 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7102 | 0.990425 | 0.991241 | 0.027583 | 0.025004 | 0.029694 | 0.027315 | 1007.888889 | 0.000000 | 0.001017 | 0 | 7102 | 0 | 0.000057 | 0.000000 | 0.005010 | 0.000029 | 0.002539 | 3705.100040 | 494.019755 | 71.020000 | 0.000000 | 69.609884 | 140.629884 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7140 | 0.989356 | 0.993179 | 0.027239 | 0.025004 | 0.029000 | 0.027175 | 1027.555556 | 0.000000 | 0.001038 | 0 | 7140 | 0 | 0.000049 | 0.000000 | 0.004414 | 0.000024 | 0.002226 | 6640.199979 | 556.741793 | 71.400000 | 0.000000 | 58.112068 | 129.512068 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7222 | 0.989615 | 0.988555 | 0.027426 | 0.025004 | 0.031564 | 0.026656 | 1024.444444 | 0.000000 | 0.001035 | 0 | 7222 | 0 | 0.000057 | 0.000000 | 0.004781 | 0.000028 | 0.002383 | 2941.699990 | 521.401939 | 72.220000 | 0.000000 | 61.611828 | 133.831828 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7222 | 0.990446 | 0.988701 | 0.027331 | 0.025004 | 0.030345 | 0.027734 | 1028.111111 | 0.000000 | 0.001038 | 0 | 7222 | 0 | 0.000049 | 0.000000 | 0.004577 | 0.000024 | 0.002282 | 3736.200044 | 513.658058 | 72.220000 | 0.000000 | 61.112152 | 133.332152 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7148 | 0.992445 | 0.995828 | 0.027495 | 0.025004 | 0.030029 | 0.027500 | 1026.888889 | 0.000000 | 0.001034 | 0 | 7148 | 0 | 0.000054 | 0.000000 | 0.004858 | 0.000027 | 0.002447 | 4944.599990 | 516.946685 | 71.480000 | 0.000000 | 63.611660 | 135.091660 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7248 | 0.988549 | 0.993017 | 0.027399 | 0.025004 | 0.030390 | 0.026929 | 1033.111111 | 0.000000 | 0.001044 | 0 | 7248 | 0 | 0.000047 | 0.000000 | 0.004749 | 0.000023 | 0.002359 | 4113.300005 | 519.000414 | 72.480000 | 0.000000 | 63.112752 | 135.592752 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7205 | 0.990840 | 0.994475 | 0.027182 | 0.025004 | 0.027647 | 0.027686 | 1033.222222 | 0.000000 | 0.001042 | 0 | 7205 | 0 | 0.000038 | 0.000000 | 0.004280 | 0.000019 | 0.002139 | 8560.799994 | 507.788591 | 72.050000 | 0.000000 | 58.612524 | 130.662524 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7237 | 0.990051 | 0.991968 | 0.027416 | 0.025004 | 0.031311 | 0.027120 | 1043.111111 | 0.000000 | 0.001053 | 0 | 7237 | 0 | 0.000052 | 0.000000 | 0.004771 | 0.000026 | 0.002373 | 3374.900029 | 507.944300 | 72.370000 | 0.000000 | 63.113736 | 135.483736 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7371 | 0.989282 | 0.996099 | 0.027164 | 0.025004 | 0.030086 | 0.027317 | 1065.555556 | 0.000000 | 0.001075 | 0 | 7371 | 0 | 0.000050 | 0.000000 | 0.004336 | 0.000025 | 0.002118 | 7593.000017 | 516.185009 | 73.710000 | 0.000000 | 54.616136 | 128.326136 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7152 | 0.990632 | 0.986523 | 0.027527 | 0.025004 | 0.030788 | 0.028172 | 1031.222222 | 0.000000 | 0.001042 | 0 | 7152 | 0 | 0.000042 | 0.000000 | 0.005004 | 0.000021 | 0.002519 | 4297.000007 | 537.846365 | 71.520000 | 0.000000 | 68.112536 | 139.632536 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7169 | 0.989259 | 0.983607 | 0.027443 | 0.025004 | 0.031656 | 0.027632 | 1008.000000 | 0.000000 | 0.001020 | 0 | 7169 | 0 | 0.000042 | 0.000000 | 0.004855 | 0.000021 | 0.002438 | 2473.700035 | 506.681782 | 71.690000 | 0.000000 | 62.610184 | 134.300184 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7194 | 0.990409 | 0.991098 | 0.027510 | 0.025004 | 0.031048 | 0.026534 | 1014.333333 | 0.000000 | 0.001024 | 0 | 7194 | 0 | 0.000042 | 0.000000 | 0.005027 | 0.000021 | 0.002515 | 3065.600002 | 514.399166 | 71.940000 | 0.000000 | 67.110592 | 139.050592 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7304 | 0.991238 | 0.989071 | 0.027249 | 0.025004 | 0.030219 | 0.027384 | 1045.777778 | 0.000000 | 0.001056 | 0 | 7304 | 0 | 0.000042 | 0.000000 | 0.004504 | 0.000021 | 0.002220 | 3401.800001 | 508.562418 | 73.040000 | 0.000000 | 56.614000 | 129.654000 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7260 | 0.990358 | 0.990753 | 0.027507 | 0.025004 | 0.029936 | 0.027683 | 1048.888889 | 0.000000 | 0.001059 | 0 | 7260 | 0 | 0.000044 | 0.000000 | 0.005015 | 0.000022 | 0.002487 | 2643.199987 | 509.909862 | 72.600000 | 0.000000 | 66.114372 | 138.714372 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7189 | 0.989706 | 0.991465 | 0.027349 | 0.025004 | 0.029621 | 0.027585 | 1022.888889 | 0.000000 | 0.001033 | 0 | 7189 | 0 | 0.000045 | 0.000000 | 0.004592 | 0.000022 | 0.002299 | 8124.099986 | 510.737821 | 71.890000 | 0.000000 | 56.611576 | 128.501576 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7135 | 0.990610 | 0.997241 | 0.027266 | 0.025004 | 0.028553 | 0.026714 | 1026.333333 | 0.000000 | 0.001034 | 0 | 7135 | 0 | 0.000060 | 0.000000 | 0.004442 | 0.000030 | 0.002241 | 6004.900031 | 508.099047 | 71.350000 | 0.000000 | 59.611720 | 130.961720 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7271 | 0.990648 | 0.994406 | 0.027463 | 0.025004 | 0.032520 | 0.027492 | 1037.333333 | 0.000000 | 0.001046 | 0 | 7271 | 0 | 0.000055 | 0.000000 | 0.004892 | 0.000027 | 0.002422 | 3920.299991 | 506.633874 | 72.710000 | 0.000000 | 64.112980 | 136.822980 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7329 | 0.990312 | 0.989189 | 0.027414 | 0.025004 | 0.030363 | 0.027286 | 1050.444444 | 0.000000 | 0.001061 | 0 | 7329 | 0 | 0.000055 | 0.000000 | 0.004810 | 0.000027 | 0.002363 | 4219.199996 | 516.308773 | 73.290000 | 0.000000 | 62.114588 | 135.404588 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7147 | 0.988946 | 0.986745 | 0.027518 | 0.025004 | 0.030687 | 0.026945 | 1008.666667 | 0.000000 | 0.001020 | 0 | 7147 | 0 | 0.000051 | 0.000000 | 0.004941 | 0.000026 | 0.002489 | 3808.300011 | 516.935190 | 71.470000 | 0.000000 | 66.110208 | 137.580208 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7009 | 0.991582 | 0.988355 | 0.027497 | 0.025004 | 0.030447 | 0.027410 | 998.555556 | 0.000000 | 0.001008 | 0 | 7009 | 0 | 0.000053 | 0.000000 | 0.004790 | 0.000027 | 0.002460 | 4090.999952 | 520.471537 | 70.090000 | 0.000000 | 63.108840 | 133.198840 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7129 | 0.988919 | 0.987342 | 0.027539 | 0.025004 | 0.032576 | 0.028286 | 1017.333333 | 0.000000 | 0.001029 | 0 | 7129 | 0 | 0.000045 | 0.000000 | 0.004948 | 0.000022 | 0.002499 | 9773.900034 | 546.884332 | 71.290000 | 0.000000 | 64.111144 | 135.401144 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7111 | 0.988047 | 0.985215 | 0.027578 | 0.025004 | 0.031616 | 0.026683 | 1025.000000 | 0.000000 | 0.001038 | 0 | 7111 | 0 | 0.000055 | 0.000000 | 0.004980 | 0.000028 | 0.002521 | 3375.400032 | 526.431978 | 71.110000 | 0.000000 | 70.112104 | 141.222104 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7103 | 0.992679 | 0.992701 | 0.027805 | 0.025004 | 0.031772 | 0.027742 | 1010.111111 | 0.000000 | 0.001018 | 0 | 7103 | 0 | 0.000052 | 0.000000 | 0.005438 | 0.000026 | 0.002756 | 22453.099955 | 520.520780 | 71.030000 | 0.000000 | 72.109896 | 143.139896 | 0 | 0 | 0 |
| J_OVERHEAD | AHP | 7186 | 0.988311 | 0.988966 | 0.027262 | 0.025004 | 0.029533 | 0.027310 | 1028.111111 | 0.000000 | 0.001040 | 0 | 7186 | 0 | 0.000048 | 0.000000 | 0.004434 | 0.000024 | 0.002221 | 4209.900042 | 509.000223 | 71.860000 | 0.000000 | 58.112332 | 129.972332 | 0 | 0 | 0 |

The four matrices are generated as pairwise ratios of preselected design-weight vectors. CR is zero (within floating-point precision) by construction; this is a mathematical consistency check, not evidence that the preferences were elicited from domain experts.

## Selection and Pareto-Dominance Diagnostics

| AHP_State | Total_Decisions | NB_Sel | 5G_Sel | Dom_NB | Dom_5G | Dom_None | Single_Feas | NB_Selection_Pct | 5G_Selection_Pct | Single_Feasible_Pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CONFLICT | 128888 | 0 | 128888 | 0 | 0 | 0 | 128888 | 0.000000 | 100.000000 | 100.000000 |
| EMERGENCY | 616288 | 0 | 616288 | 0 | 0 | 0 | 616288 | 0.000000 | 100.000000 | 100.000000 |
| LOW_BATTERY | 302258 | 0 | 302258 | 0 | 302258 | 0 | 0 | 0.000000 | 100.000000 | 0.000000 |
| NORMAL | 4720741 | 0 | 4720741 | 0 | 4524859 | 194210 | 1672 | 0.000000 | 100.000000 | 0.035418 |
| OVERALL | 5768175 | 0 | 5768175 | 0 | 4827117 | 194210 | 746848 | 0.000000 | 100.000000 | 12.947735 |

The denominator is 5,768,175 actual AHP ranking invocations, not all generated packets. A packet that fails the hard feasibility filter for both candidates does not invoke AHP-TOPSIS and is therefore outside this denominator. The per-call categories form an exhaustive partition: both feasible (5,021,327) plus only one feasible (746,848) equals 5,768,175.

| Category | Decision count | % of all AHP ranking calls | % of both-feasible calls |
| --- | --- | --- | --- |
| 5G dominates NB-IoT | 4,827,117 | 83.69% | 96.13% |
| NB-IoT dominates 5G | 0 | 0.00% | 0.00% |
| Neither dominates | 194,210 | 3.37% | 3.87% |
| Only one candidate feasible | 746,848 | 12.95% | Not applicable |

Pareto method: compare only calls where both candidates pass the hard QoS feasibility filter. Latency and candidate marginal energy are minimized; configured reliability and nominal bandwidth are maximized. Candidate X dominates candidate Y when X is no worse on all four criteria and strictly better on at least one. The mutually exclusive categories are 5G_DOM, NB_DOM, and NO_DOM for two-feasible calls; SINGLE_FEASIBLE is reported separately and is not a pairwise Pareto comparison. No-feasible packets are filtered before an AHP ranking call and are not represented in the selection-analysis denominator.

`NO_DOM` does not mean that the candidates are equal: in these records each alternative has at least one criterion advantage. TOPSIS still selected 5G in these calls. Do not claim that 5G Pareto-dominates every individual decision.

The 5G dominance rate is 83.69% of all AHP ranking invocations; equivalently, it is 96.13% of calls in which both alternatives are feasible. The 3.37% neither-dominates rate is 3.87% of two-feasible calls. These denominators answer different questions and must not be conflated.

## Initial-Sleep Candidate Inputs

| State | Packet / deadline | Candidate | Predicted latency (s; minimize) | Marginal energy (J; minimize) | Configured reliability (%; maximize) | Nominal bandwidth (bps; maximize) | Feasible at initial sleep |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NORMAL | 50 B / 10 s | NB-IoT | 2.006061 | 1.506061 | 95 | 66,000 | Yes |
| NORMAL | 50 B / 10 s | 5G NR | 0.120004 | 0.500012 | 99 | 100,000,000 | Yes |
| LOW_BATTERY | 50 B / 10 s | NB-IoT | 2.006061 | 1.506061 | 95 | 66,000 | Yes |
| LOW_BATTERY | 50 B / 10 s | 5G NR | 0.120004 | 0.500012 | 99 | 100,000,000 | Yes |
| EMERGENCY | 200 B / 1 s | NB-IoT | 2.024242 | 1.524242 | 95 | 66,000 | No |
| EMERGENCY | 200 B / 1 s | 5G NR | 0.120016 | 0.500048 | 99 | 100,000,000 | Yes |
| CONFLICT | 200 B / 1 s | NB-IoT | 2.024242 | 1.524242 | 95 | 66,000 | No |
| CONFLICT | 200 B / 1 s | 5G NR | 0.120016 | 0.500048 | 99 | 100,000,000 | Yes |

The table displays the source-derived candidate values for representative packet/state pairs. Predicted latency = setup delay + base latency + serialization time. Initial-sleep marginal energy = setup energy + transmit power × serialization time. Values are model inputs/derived estimates, not physical measurements; the energy estimate represents a candidate decision at initial sleep and does not forecast future modem wake-up cycles, queue evolution, CPU energy, or the full simulation horizon. For normal/low-battery telemetry, the representative packet is 50 B with a 10 s deadline; emergency/conflict uses 200 B with a 1 s deadline.

## Paired Statistical Comparisons

| Metric | Paired comparison records | Estimable paired t-tests | Identical zero-difference pairs (not tested) | Other non-estimable | t-test BH family size | Wilcoxon BH family size | t-test BH q < 0.05 | Wilcoxon BH q < 0.05 | Shapiro p < 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PDR | 120 | 24 | 96 | 0 | 24 | 24 | 24 | 24 | 2 |
| Avg_Lat_s | 120 | 24 | 96 | 0 | 24 | 24 | 24 | 24 | 0 |
| Total_Eng_J | 120 | 24 | 96 | 0 | 24 | 24 | 24 | 24 | 1 |

For each scenario and non-AHP strategy, the primary parametric comparison is a two-sided paired Student t-test, implemented equivalently as a one-sample t-test on per-seed differences (candidate minus AHP). Pairs are matched by scenario and seed. The 95% confidence interval is t-based; paired Cohen's dz is mean difference divided by the sample standard deviation of differences. The inferential model assumes independent seed replicates and an approximately normal distribution of paired differences. Shapiro-Wilk is included as an exploratory diagnostic, not as proof of normality.

A sample with exactly zero variance in its paired differences has no estimable Student-t statistic, p-value, t-based confidence interval, or Cohen's dz. In particular, an all-zero difference vector is a descriptive identity, not a valid p=1.0 test result. These cells retain their zero mean and observed min/max but have inferential fields left blank (NaN). The same treatment is applied to constant nonzero differences. AHP-versus-AHP self-comparisons remain in the 144-row paired summary but are explicitly marked SELF_COMPARISON_NOT_TESTED.

The Wilcoxon signed-rank test (two-sided; zero paired differences omitted) is supplied as a non-parametric sensitivity analysis for estimable comparisons; SciPy method=auto chooses exact or asymptotic calculation according to the data. Benjamini-Hochberg FDR adjustment is applied separately within each metric family and separately for the paired-t and Wilcoxon sensitivity p-values. Non-estimable cases are excluded from the corresponding FDR family rather than being assigned fabricated p-values.
The exploratory Shapiro-Wilk diagnostic fell below 0.05 for 2 of 24 estimable PDR differences, 1 of 24 energy differences, and 0 of 24 mean-latency differences. The Wilcoxon sensitivity results remained BH-significant for all 24 estimable comparisons within each metric family. This is a sensitivity check, not a claim that the seed-level model assumptions are proven.

Per metric, 120 archived comparison rows are retained in the FDR audit inventory, but only 24 paired-t p-values are estimable; 96 are exact identical-zero comparisons and are not inferential tests. The 144-row `paired_stats.csv` retains all six strategies, including AHP self-comparisons. The original raw primary results remain unchanged.

## Reproduction

Run `python experiments/audit_existing_results.py` from the project root. It reads archived raw result CSVs and regenerates `results/processed/paired_stats.csv`, diagnostic tables under `results/tables/`, and this report. It does not rerun SimPy simulations.

## Scope Notes

The primary raw archive contains 24 configurations and remains the original 24-configuration / 4,320-row dataset (30 seeds × six algorithms). The supplementary outage pilot is reported separately. Do not describe it as a 25th primary configuration or merge its records into the primary CSV. A separate supplementary 5G-outage/recovery pilot contains 30 records from 5 seeds and six algorithms. It is stored under `results/supplementary/5g_outage/` and is not included in the primary matrix.

---

## Execution guide for this repository layout

Use the repository-root `README.md` as the authoritative current installation and execution guide. The commands below reflect the final flattened directory layout.

### Windows PowerShell — Python simulation

```powershell
cd simulation
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall -q src experiments tests
python -m pytest -v
python experiments/run_experiments.py smoke
```

### Audit archived results and regenerate figures

```powershell
python experiments/audit_existing_results.py
python experiments/generate_figures.py
```

### Run the separate 5G outage pilot

```powershell
python experiments/run_5g_outage_supplementary.py --seeds 5
```

The pilot remains separate from the primary dataset. For a clean five-seed rerun, use a disposable copy and remove the five checkpoint files there before running. Do not append pilot rows to `results/raw/raw_paired_metrics.csv`.

### Full primary reproduction

```powershell
python experiments/run_experiments.py
```

This is a full 24-configuration × 30-seed × six-strategy run. Existing checkpoints may be reused. For a clean reproduction, use a separate copy and remove its relevant checkpoints/output files only in that copy. The archived primary dataset in this repository was audited, not freshly rerun during final packaging.

### Run the interactive application

```powershell
cd application
py run_app.py
```

Open `http://127.0.0.1:8000`. The optional FastAPI bridge can be started in a second terminal after installing `application/backend/requirements.txt`, using `python backend/run_api.py`.

### Validation status and boundaries

The current browser suite contains 19 Node tests. The project's Python validation record reports 25 tests; this packaging environment could not rerun the full SimPy-dependent Python suite because SimPy was unavailable and package-index access was blocked. Fifteen Python tests that do not require SimPy were rerun successfully during packaging. The application verifier, Python compilation, browser tests and local HTTP resource checks passed. No full 4,320-run primary experiment was rerun during packaging.

The simulator does not implement a complete 3GPP EPC/5GC, N3IWF, ATSSS, LoRaWAN PHY/MAC, physical radio propagation, hardware modem or 6G protocol stack. 6G is future scope only. AHP weights are design-specified; zero consistency ratio verifies matrix construction, not expert validation. Candidate energy is an instantaneous marginal estimate, not a horizon-aware forecast.
