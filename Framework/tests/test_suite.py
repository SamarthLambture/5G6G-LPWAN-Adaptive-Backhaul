import pytest
import simpy
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.core.math_engine import DynamicAHP, TOPSIS
from src.simulation.network import BackhaulModem, EdgeGateway
from src.core.algorithms import AdapAHP

def test_ahp_reciprocity_and_cr():
    ahp = DynamicAHP()
    for s in ["NORMAL", "EMERGENCY", "LOW_BATTERY", "CONFLICT"]:
        m = ahp.matrices[s]
        assert ahp.validate_matrix(m)
        w, cr = ahp.calculate_weights(m)
        assert cr < 0.10
        assert np.isclose(np.sum(w), 1.0)

def test_ahp_synthetic_tradeoff():
    algo = AdapAHP()
    dm = np.array([
        [500, 1.5, 95, 66000],  # NB
        [20, 10.0, 99, 100000]  # 5G (synthetic high energy)
    ])
    # Normal (Prefers energy): NB should win
    sel_norm = algo.select_network([0, 1], dm, False, 100.0)
    # Emergency (Prefers latency): 5G should win
    sel_emerg = algo.select_network([0, 1], dm, True, 100.0)
    assert sel_norm == 0
    assert sel_emerg == 1

def test_topsis_dynamic_tie():
    topsis = TOPSIS()
    m = np.array([[10, 20], [20, 10]]) 
    w = np.array([0.5, 0.5])
    # Energy is index 0. A1 energy=10, A2 energy=20. A1 should win.
    res = topsis.rank_alternatives(m, w, [-1, -1], ["energy", "latency"])
    assert res == 0 

def test_outage_sleep():
    env = simpy.Environment()
    class MockGW: 
        battery_j = 100.0
        def update_status(self, p, s): p['status'] = s
        def update_stage(self, p, s): pass
    gw = MockGW()
    m = BackhaulModem(env, gw, "NB", 1000, 0.1, 1.0, 5.0, 1.0, 2.0, 100)

    def trig():
        yield env.timeout(1)
        m.trigger_outage()

    env.process(trig())
    env.run(until=5)
    assert m.state == "SLEEP"

def test_outage_waking_safe_release():
    env = simpy.Environment()
    class MockGW: 
        battery_j = 100.0; results = []
        def update_status(self, p, s): p['status'] = s
        def update_stage(self, p, s): pass
    gw = MockGW()
    m = BackhaulModem(env, gw, "NB", 100, 0, 2.0, 5.0, 1.0, 2.0, 100) # 2s setup

    p1 = {'pid': 1, 'payload': 100, 'arr': 0, 'rel_roll': {'NB': 0}, 'lat_pred_sel': 0, 'ts_enter_bh_q': 0}
    m.add_packet(p1)

    def outage_trigger():
        yield env.timeout(1) # Interrupt halfway through setup
        m.trigger_outage()
        yield env.timeout(10)
        m.recover_outage()

    env.process(outage_trigger())
    env.run(until=15)

    assert p1['status'] == "DROP_OUTAGE"
    assert len(m.queue) == 0
    assert m.state == "SLEEP"
    assert m.avail == True
    # Gateway battery correctly drained by setup energy 5.0J upon entering WAKING
    assert gw.battery_j == 95.0
    assert m.energy_setup_tx_j == 5.0

def test_outage_active_tx_partial_energy():
    env = simpy.Environment()
    class MockGW: 
        battery_j = 100.0; results = []
        def update_status(self, p, s): p['status'] = s
        def update_stage(self, p, s): pass
    gw = MockGW()
    # tx_pow = 1.0W, setup_energy = 0J to isolate tx_energy
    m = BackhaulModem(env, gw, "NB", 100, 0, 0, 0, 1.0, 2.0, 100)

    p1 = {'pid': 1, 'payload': 100, 'arr': 0, 'rel_roll': {'NB': 0}, 'lat_pred_sel': 0, 'ts_enter_bh_q': 0}
    m.add_packet(p1)

    def outage_trigger():
        yield env.timeout(4.0) # Interrupt 4s into an 8s transmission
        m.trigger_outage()

    env.process(outage_trigger())
    env.run(until=10)

    assert p1['status'] == "DROP_OUTAGE"
    assert m.energy_setup_tx_j == 4.0 # 4s * 1W
    assert m.total_tx_time == 4.0
    assert gw.battery_j == 96.0

def test_outage_idle_tail():
    env = simpy.Environment()
    class MockGW: 
        battery_j = 100.0; results = []
        def update_status(self, p, s): p['status'] = s
        def update_stage(self, p, s): pass
    gw = MockGW()
    m = BackhaulModem(env, gw, "NB", 100, 0, 0, 0, 1.0, 2.0, 100)

    p1 = {'pid': 1, 'payload': 100, 'arr': 0, 'rel_roll': {'NB': 0}, 'lat_pred_sel': 0, 'ts_enter_bh_q': 0}
    m.add_packet(p1)

    def outage_trigger():
        yield env.timeout(9.0) # 8s TX finishes, modem enters 2s IDLE_TAIL. Hit at 9s.
        m.trigger_outage()

    env.process(outage_trigger())
    env.run(until=15)

    assert p1['status'] == "DELIVERED"
    assert m.state == "SLEEP"

def test_accounting_idempotent():
    env = simpy.Environment()
    class MockAlgo:
        def select_network(self, f, m, e, b): return 0 if f else -1
        def get_ahp_state(self, e, b): return "N/A"

    p = [{'pid': 1, 'payload': 100, 'arr': 0, 'emerg': False, 'rel_roll': {'NB': 0, '5G': 0}}]
    gw = EdgeGateway(env, MockAlgo(), p, [])
    env.run(until=0.001) # Stop mid-cpu processing

    gw.end_of_simulation_sweep()
    gw.end_of_simulation_sweep()

    assert len(gw.registry) == 1
    assert gw.registry[1]['status'] == "IN_FLIGHT_CPU_PROC"


def test_5g_outage_scenario_is_registered_and_recovers():
    env = simpy.Environment()

    class MockAlgo:
        def select_network(self, feasible, matrix, emergency, battery):
            return 1 if 1 in feasible else (0 if 0 in feasible else -1)
        def get_ahp_state(self, emergency, battery):
            return "N/A"

    trace = [{
        "pid": 999,
        "arr": 10_000.0,
        "emerg": False,
        "payload": 50,
        "rel_roll": {"NB": 0.0, "5G": 0.0},
    }]
    events = [{"type": "5G_OUTAGE", "start": 2000.0, "dur": 30.0}]
    gateway = EdgeGateway(env, MockAlgo(), trace, events)

    env.run(until=2000.1)
    assert gateway.a2.avail is False
    env.run(until=2030.1)
    assert gateway.a2.avail is True


def test_adaptive_gateway_uses_nb_during_5g_outage_and_returns_to_5g():
    env = simpy.Environment()
    trace = [
        {"pid": 1, "arr": 0.0, "emerg": False, "payload": 50,
         "rel_roll": {"NB": 0.0, "5G": 0.0}},
        {"pid": 2, "arr": 1.2, "emerg": False, "payload": 50,
         "rel_roll": {"NB": 0.0, "5G": 0.0}},
        {"pid": 3, "arr": 1.6, "emerg": False, "payload": 50,
         "rel_roll": {"NB": 0.0, "5G": 0.0}},
        {"pid": 4, "arr": 6.2, "emerg": False, "payload": 50,
         "rel_roll": {"NB": 0.0, "5G": 0.0}},
    ]
    events = [{"type": "5G_OUTAGE", "start": 1.0, "dur": 2.0}]
    gateway = EdgeGateway(env, AdapAHP(), trace, events)
    env.run(until=10.0)
    gateway.end_of_simulation_sweep()

    assert gateway.registry[1]["sel_net"] == 1  # 5G before outage
    assert gateway.registry[2]["sel_net"] == 0  # NB fallback during outage
    assert gateway.registry[3]["sel_net"] == 0  # NB fallback during outage
    assert gateway.registry[4]["sel_net"] == 1  # 5G after recovery
    assert gateway.switches == 2
    assert gateway.a2.avail is True
