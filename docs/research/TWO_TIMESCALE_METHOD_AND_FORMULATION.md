# Method and Formulation — Two-Timescale Adaptive Backhaul Controller

## 1. Purpose

The extension introduces a slower gateway-level backhaul preference and a faster packet-level QoS override. The original AHP-TOPSIS strategies remain available as baselines. The new controller is implemented in `Framework/src/core/two_timescale.py` and exposed as `TwoTimescale` in `Framework/src/core/algorithms.py`.

The controller is a system-level policy extension, not a new AHP or TOPSIS variant.

## 2. Timescale 1: session/burst preference

The controller groups arrivals into an analytical traffic burst using the modem's existing idle-tail timer. It estimates the inter-arrival rate using an exponentially weighted moving average (EWMA):

\[
\bar{g}_t = \alpha g_t + (1-\alpha)\bar{g}_{t-1},\qquad \hat{\lambda}_t=1/\bar{g}_t.
\]

Here, \(g_t\) is the observed inter-arrival gap, \(\alpha\) is the configurable EWMA coefficient, and \(\hat{\lambda}_t\) is the estimated packet arrival rate.

For a Poisson arrival process grouped into clusters where successive gaps do not exceed idle-tail duration \(T\), the expected cluster size is:

\[
\hat{N}_t = \min\{N_{\max},\max(1,\exp(\hat{\lambda}_t T))\}.
\]

This is a model-based expected cluster size, not a direct measurement of connection length. The estimate is capped by `maximum_expected_packets` for numerical and operational stability. The simulator's service and queue dynamics can extend radio activity beyond the arrival-gap cluster approximation; that is a limitation of this analytical forecast.

## 3. Session-energy estimate

For candidate network \(n\), the estimate used by the new selector is:

\[
\hat{E}_{n,\mathrm{packet}} =
\frac{E_{n,\mathrm{setup,due}} + \hat N_t E_{n,\mathrm{tx}} + P_{n,\mathrm{idle}}T_{\mathrm{idle}} + E_{\mathrm{switch}}}{\hat N_t}.
\]

Where:

- \(E_{n,\mathrm{setup,due}}\) is the setup energy still due now; it is nonzero when the current modem state is `SLEEP` and zero when the modem is already `WAKING`, `ACTIVE` or in `IDLE_TAIL`.
- \(E_{n,\mathrm{tx}}\) is the model's transmit energy for one packet.
- \(P_{n,\mathrm{idle}}T_{\mathrm{idle}}\) is an optional idle-energy term.
- \(E_{\mathrm{switch}}\) is an optional switching-energy term charged to a challenger.
- \(\hat N_t\) is the expected packet count in the predicted arrival burst.

The original simulator does not define idle-tail power or switching energy. Accordingly, both optional terms default to zero. Nonzero values require measurement or explicit sensitivity assumptions and must not be represented as measured device characteristics.

The session controller selects the minimum estimated energy-per-packet candidate among the candidates already judged feasible by the gateway. Latency is used as a deterministic tie-break.

## 4. Timescale 2: packet-level QoS override

The existing gateway first builds its feasible set from network availability and the predicted packet deadline:

\[
\mathcal F(p)=\{n: A_n=1\land \hat D_{p,n}\leq d_p\}.
\]

An optional reliability threshold can be enabled through `minimum_reliability_pct`; it is disabled by default because the archived model did not previously use configured reliability as a hard feasibility constraint.

For an emergency packet, the packet-level controller selects the feasible candidate with minimum predicted latency (with reliability and transmit energy as tie-breaks). This temporary override does not change the persistent session preference. A routine packet uses the session preference while it remains feasible.

## 5. Switching stability

The controller supports:

- A minimum dwell time (`minimum_dwell_s`).
- A minimum relative improvement (`improvement_threshold`).
- Forced fallback when the session preference is no longer feasible.
- Temporary emergency overrides that do not count as persistent preference switches.
- A counter that distinguishes persistent controller switches from packet overrides.

A candidate can replace a still-feasible preferred network only after dwell time has elapsed and the candidate's estimated energy cost meets the configured improvement threshold. The default configuration uses a 2-second dwell and a 10% relative-improvement threshold. These are configurable design parameters, not tuned or statistically optimized values.

## 6. Decision procedure

```text
On each packet decision:
    Update inter-arrival EWMA and detect whether the prior burst ended.
    Read the gateway's feasible candidate set.
    If no candidate is feasible: reject the packet.
    If an optional reliability threshold is configured:
        Remove candidates below the threshold.
    If packet is emergency:
        Select the lowest-latency feasible candidate.
        Record a packet-level override if it differs from session preference.
        Do not change session preference.
    Otherwise:
        Estimate expected packets in the current Poisson burst.
        Compute setup-amortized energy per packet for each feasible candidate.
        If this is a new burst or no preference exists:
            Select the lowest-energy feasible candidate.
        Else if current preference is infeasible:
            Force fallback to the lowest-energy feasible candidate.
        Else:
            Hold current preference unless a challenger is materially better
            and the minimum dwell time has elapsed.
        Record decision reason, costs, and switch type.
```

## 7. Integration with the existing simulator

`BackhaulModem.selection_energy_context()` exposes the current modem state, setup energy due now, transmit energy, tail timer, latency, configured reliability and nominal bandwidth. The `EdgeGateway` checks whether the selected algorithm implements `select_network_with_context`. Existing algorithms retain their original `select_network` call path and behaviour.

The new selector is available as `TwoTimescale` for direct use in SimPy. A short paired validation runner is provided at `Framework/experiments/run_two_timescale_smoke.py`.

## 8. Scope boundaries

The new controller does not implement:

- Hardware-calibrated modem energy profiles.
- Idle-tail power measurements.
- 3GPP-standardized handover or ATSSS.
- A physical LoRaWAN/5G deployment.
- A probabilistic delay distribution where the original model only exposes deterministic estimates.
- Reinforcement learning or trained traffic prediction.

The work is a simulation-based, gateway-selection policy extension.


## 9. Multi-operating-point evaluation

The implementation was evaluated by a paired 30-condition SimPy matrix (five offered loads, two emergency shares, three outage patterns, 30 seeds each). Full condition-wise statistics and interpretation boundaries are in `Framework/results/supplementary/two_timescale/multi_operating_point/DETAILED_MATRIX_ANALYSIS.md`. The matrix shows that TSC's compute-time advantage is broad, while end-to-end latency benefits are conditional on repeated outages at 2–4 packets/s. It does not establish a PDR, emergency-PDR, switching or overall energy benefit.
