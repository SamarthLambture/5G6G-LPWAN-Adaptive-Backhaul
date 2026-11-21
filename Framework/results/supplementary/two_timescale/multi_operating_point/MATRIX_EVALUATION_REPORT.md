# Multi-Operating-Point TSC Evaluation

- Status: `completed`
- Offered loads: [0.5, 1.0, 2.0, 4.0, 8.0] packets/s
- Emergency shares: [0.1, 0.25]
- Outage patterns: ['none', 'single', 'repeated']
- Paired seeds per condition: 30
- Conditions: 30
- Hypothesis tests after pairing: 180
- Wall runtime: 330.895 s
- Paired method: same generated input trace for AHP-TOPSIS and TSC within each seed/condition.
- Multiple testing: Holm correction across every metric × operating-condition test in this matrix.

## Interpretation boundary

This is a simulation matrix under the configured abstraction, not physical modem validation. The current run excludes idle-tail power and calibrated switching energy. Interpret every condition separately and include losses or regressions; do not select only favourable operating points.

See `matrix_paired_statistics.csv` for paired differences, confidence intervals, raw and Holm-adjusted p-values, and better/tied/worse seed counts.