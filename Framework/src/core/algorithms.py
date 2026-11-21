import numpy as np
from .math_engine import DynamicAHP, TOPSIS
from .two_timescale import TwoTimescaleConfig, TwoTimescaleController, load_two_timescale_config

class BaseAlgo:
    def select_network(self, f, m, e, b): pass
    def get_ahp_state(self, e, b): return "N/A"
class FixedNB(BaseAlgo):
    def select_network(self, f, m, e, b): return 0 if 0 in f else -1
class Fixed5G(BaseAlgo):
    def select_network(self, f, m, e, b): return 1 if 1 in f else -1
class LatFirst(BaseAlgo):
    def select_network(self, f, m, e, b): return f[np.argmin([m[i,0] for i in f])] if f else -1
class EnerFirst(BaseAlgo):
    def select_network(self, f, m, e, b): return f[np.argmin([m[i,1] for i in f])] if f else -1

class StatTOP(BaseAlgo):
    def __init__(self):
        self.top = TOPSIS()
        self.crit = [-1, -1, 1, 1]
        self.names = ["latency", "energy", "reliability", "bandwidth"]
    def select_network(self, f, m, e, b):
        if not f: return -1
        return f[self.top.rank_alternatives(m[f], np.array([0.25]*4), self.crit, self.names)]

class AdapAHP(BaseAlgo):
    def __init__(self):
        self.ahp, self.top = DynamicAHP(), TOPSIS()
        self.crit = [-1, -1, 1, 1]
        self.names = ["latency", "energy", "reliability", "bandwidth"]
    def select_network(self, f, m, e, b):
        if not f: return -1
        w, _ = self.ahp.get_state_weights(e, b)
        return f[self.top.rank_alternatives(m[f], w, self.crit, self.names)]
    def get_ahp_state(self, e, b):
        return self.ahp.get_state(e, b)


class TwoTimescale(BaseAlgo):
    """Session-preference controller with packet-level QoS overrides.

    The integrated EdgeGateway detects ``select_network_with_context`` and
    supplies modem lifecycle energy components. The legacy ``select_network``
    method remains available for simple callers and tests.
    """

    def __init__(self, config=None):
        self.controller = TwoTimescaleController(config or load_two_timescale_config())

    @property
    def last_decision(self):
        return self.controller.last_decision

    def select_network(self, f, m, e, b):
        return self.controller.select_network(f, m, e, b)

    def select_network_with_context(self, f, m, e, b, **context):
        return self.controller.select_network_with_context(f, m, e, b, **context)

    def get_ahp_state(self, e, b):
        return self.controller.get_ahp_state(e, b)
