import simpy
import numpy as np
import time
from collections.abc import Callable, Sequence
from typing import Any

from src.core.backhaul_interface import (
    DEFAULT_BACKHAUL_CATALOG,
    RuntimeBackhaulMetrics,
    BackhaulCatalog,
    BackhaulAdapter,
    validate_backhaul_adapters,
)

class BackhaulModem:
    def __init__(self, env, gateway, name, bw, base_lat, set_time, set_energy, tx_pow, tail_timer, rel, profile_id=None):
        self.env = env
        self.gateway = gateway
        self.name = name
        self.profile_id = profile_id or ("nb_iot" if name == "NB" else "5g_nr")
        self.profile = DEFAULT_BACKHAUL_CATALOG.get(self.profile_id)
        if not self.profile.is_simulation_selectable:
            raise ValueError(f"Backhaul profile {self.profile_id} is not enabled for simulation")

        self.bw = bw
        self.base_lat = base_lat
        self.set_time = set_time
        self.set_energy = set_energy
        self.tx_pow = tx_pow
        self.tail_time = tail_timer
        self.rel = rel

        self.queue = []
        self.max_q = 500

        self.state = "SLEEP"
        self.avail = True

        self.active_packet = None
        self.active_tx_end = 0
        self.wake_end_time = 0

        self.energy_setup_tx_j = 0.0
        self.setup_count = 0
        self.total_tx_time = 0.0

        self.q_area = 0.0
        self.last_q_time = 0.0

        self.packet_arrived_event = env.event()
        self.process_loop = env.process(self._fsm_loop())

    def _svc_time(self, payload):
        return ((payload * 8) / self.bw) + self.base_lat

    def estimate_delay(self, cand_payload):
        q_time = sum(self._svc_time(p['payload']) for p in self.queue)
        rem_active = max(0, self.active_tx_end - self.env.now)
        setup_pen = 0
        if self.state == "SLEEP": setup_pen = self.set_time
        elif self.state == "WAKING": setup_pen = max(0, self.wake_end_time - self.env.now)
        return q_time + rem_active + setup_pen + self._svc_time(cand_payload)

    def estimate_energy(self, payload):
        tx_time = (payload * 8) / self.bw
        e_tx = self.tx_pow * tx_time
        e_setup = self.set_energy if self.state == "SLEEP" else 0
        return e_setup + e_tx

    def selection_energy_context(self, payload, predicted_latency):
        """Expose modelled energy components without changing baseline estimates."""
        tx_time = (payload * 8) / self.bw
        tx_energy = self.tx_pow * tx_time
        setup_due = self.set_energy if self.state == "SLEEP" else 0.0
        metrics = RuntimeBackhaulMetrics(
            latency_s=float(predicted_latency),
            tx_energy_j=float(tx_energy),
            setup_energy_j=float(self.set_energy),
            setup_energy_due_j=float(setup_due),
            reliability_pct=float(self.rel),
            bandwidth_bps=float(self.bw),
            tail_time_s=float(self.tail_time),
            available=bool(self.avail),
            modem_state=str(self.state),
            tx_time_s=float(tx_time),
            provenance="configured_simulation_parameter_estimate",
        )
        context = DEFAULT_BACKHAUL_CATALOG.build_selection_context(self.profile_id, metrics)
        # The legacy model has no modem idle-tail power parameter.
        context["idle_power_modelled"] = False
        return context

    def _update_q_area(self):
        self.q_area += len(self.queue) * (self.env.now - self.last_q_time)
        self.last_q_time = self.env.now

    def _fsm_loop(self):
        while True:
            if not self.avail:
                self._update_q_area()
                for p in list(self.queue):
                    self.gateway.update_status(p, "DROP_OUTAGE")
                self.queue.clear()
                try:
                    yield self.env.timeout(999999) 
                except simpy.Interrupt as i:
                    if i.cause == "RECOVER": pass
                continue

            if not self.queue:
                if self.state == "ACTIVE":
                    self.state = "IDLE_TAIL"
                    try:
                        res = yield self.env.any_of([self.env.timeout(self.tail_time), self.packet_arrived_event])
                        if self.packet_arrived_event in res:
                            self.state = "ACTIVE"
                            self.packet_arrived_event = self.env.event()
                        else:
                            self.state = "SLEEP"
                    except simpy.Interrupt as i:
                        if i.cause == "OUTAGE": self.state = "SLEEP"
                else:
                    self.state = "SLEEP"
                    try:
                        yield self.packet_arrived_event
                        self.packet_arrived_event = self.env.event()
                    except simpy.Interrupt as i:
                        if i.cause == "OUTAGE": pass
            else:
                if self.state == "SLEEP":
                    self.state = "WAKING"
                    self.wake_end_time = self.env.now + self.set_time

                    self.setup_count += 1
                    self.energy_setup_tx_j += self.set_energy
                    self.gateway.battery_j = max(0, self.gateway.battery_j - self.set_energy)

                    try:
                        yield self.env.timeout(self.set_time)
                        self.state = "ACTIVE"
                    except simpy.Interrupt as i:
                        if i.cause == "OUTAGE":
                            self.state = "SLEEP"
                            continue

                if self.state == "WAKING":
                    try:
                        yield self.env.timeout(max(0, self.wake_end_time - self.env.now))
                    except simpy.Interrupt as i:
                        if i.cause == "OUTAGE": self.state = "SLEEP"
                    continue

                self.state = "ACTIVE"
                self._update_q_area()
                packet = self.queue.pop(0)
                packet['bh_q_delay'] = self.env.now - packet['ts_enter_bh_q']
                self.active_packet = packet
                self.gateway.update_status(packet, "IN_FLIGHT_TX")

                tx_time = (packet['payload'] * 8) / self.bw
                svc_time = tx_time + self.base_lat
                self.active_tx_end = self.env.now + svc_time
                tx_start = self.env.now

                try:
                    yield self.env.timeout(svc_time)

                    roll = packet['rel_roll'].get(self.name, 100)
                    if roll > self.rel:
                        self.gateway.update_status(packet, "DROP_RELIABILITY")
                    else:
                        packet['lat_actual'] = self.env.now - packet['arr']
                        packet['lat_error'] = packet['lat_actual'] - packet['lat_pred_sel']
                        self.gateway.update_status(packet, "DELIVERED")

                    e_tx = self.tx_pow * tx_time
                    self.energy_setup_tx_j += e_tx
                    self.total_tx_time += tx_time
                    self.gateway.battery_j = max(0, self.gateway.battery_j - e_tx)

                except simpy.Interrupt as i:
                    if i.cause == "OUTAGE":
                        elapsed = self.env.now - tx_start
                        elapsed_tx = min(elapsed, tx_time) 
                        partial_e = self.tx_pow * elapsed_tx
                        self.energy_setup_tx_j += partial_e
                        self.total_tx_time += elapsed_tx
                        self.gateway.battery_j = max(0, self.gateway.battery_j - partial_e)
                        self.gateway.update_status(packet, "DROP_OUTAGE")
                        self.state = "SLEEP"
                finally:
                    self.active_packet = None
                    self.active_tx_end = 0

    def add_packet(self, packet):
        self._update_q_area()
        if len(self.queue) >= self.max_q:
            self.gateway.update_status(packet, "DROP_QUEUE_OVERFLOW_BH")
            return False
        packet['ts_enter_bh_q'] = self.env.now
        self.gateway.update_status(packet, "IN_FLIGHT_BH_Q")
        self.queue.append(packet)
        if not self.packet_arrived_event.triggered:
            self.packet_arrived_event.succeed()
        return True

    def trigger_outage(self):
        self.avail = False
        if self.process_loop.is_alive:
            self.process_loop.interrupt(cause="OUTAGE")

    def recover_outage(self):
        self.avail = True
        if self.process_loop.is_alive:
            self.process_loop.interrupt(cause="RECOVER")


class EdgeGateway:
    def __init__(
        self,
        env,
        algo,
        trace,
        events,
        *,
        backhaul_adapter_factory: Callable[[Any, Any], Sequence[BackhaulAdapter]] | None = None,
        backhaul_catalog: BackhaulCatalog | None = None,
    ):
        self.env = env
        self.algo = algo
        self.events = events

        self.cpu = simpy.Resource(env, 1)
        self.cpu_q = []
        self.max_cpu_q = 1000
        self.cpu_q_area = 0.0
        self.last_cpu_q_time = 0.0

        self.battery_j = 10000.0
        self.max_batt = 10000.0
        self.cpu_energy_consumed = 0.0

        self.backhaul_catalog = backhaul_catalog or DEFAULT_BACKHAUL_CATALOG
        if backhaul_adapter_factory is None:
            # Baseline Parameters: NB-IoT=1.5J setup, 5G=0.5J setup. Strictly preserved.
            adapters = [
                BackhaulModem(env, self, "NB", 66000, 0.5, 1.5, 1.5, 1.0, 2.0, 95.0, profile_id="nb_iot"),
                BackhaulModem(env, self, "5G", 100000000, 0.02, 0.1, 0.5, 3.0, 2.0, 99.0, profile_id="5g_nr"),
            ]
        else:
            # Extension point: custom factories may provide extra implemented
            # adapters. Exploratory 6G templates remain blocked by the catalog.
            adapters = list(backhaul_adapter_factory(env, self))
        self.backhauls = list(validate_backhaul_adapters(adapters, self.backhaul_catalog))
        self.backhaul_by_profile = {modem.profile_id: modem for modem in self.backhauls}
        # Compatibility aliases required by the current baseline experiment
        # scripts; selection and candidate construction use self.backhauls.
        self.a1 = self.backhaul_by_profile["nb_iot"]
        self.a2 = self.backhaul_by_profile["5g_nr"]

        # UNIQUE ID & COUNT VERIFICATION
        pids = [p['pid'] for p in trace]
        assert len(set(pids)) == len(trace), "CRITICAL: Trace contains duplicate packet IDs."
        assert len(trace) > 0, "CRITICAL: Trace is empty."

        self.registry = {}
        for p in trace:
            p['stage'] = 'GENERATED'
            p['status'] = 'PENDING'
            p['algo_time_us'] = float('nan')
            p['cpu_q_delay'] = float('nan')
            p['bh_q_delay'] = float('nan')
            self.registry[p['pid']] = p

        self.prev_network = -1
        self.switches = 0
        self.decision_log = []

        env.process(self.run_trace())
        env.process(self.run_events())

    def _update_cpu_q_area(self):
        self.cpu_q_area += len(self.cpu_q) * (self.env.now - self.last_cpu_q_time)
        self.last_cpu_q_time = self.env.now

    def update_stage(self, packet, stage):
        self.registry[packet['pid']]['stage'] = stage

    def update_status(self, packet, status):
        self.registry[packet['pid']]['status'] = status
        if status.startswith("IN_FLIGHT_"):
            self.registry[packet['pid']]['stage'] = status

    def run_events(self):
        for ev in self.events:
            yield self.env.timeout(max(0, ev['start'] - self.env.now))
            if ev['type'] == "E_LAT_DEGRADE":
                modem = self.backhaul_by_profile["5g_nr"]
                old_lat = modem.base_lat
                modem.base_lat = 0.150
                yield self.env.timeout(ev['dur'])
                modem.base_lat = old_lat
            elif ev['type'] == "NB_OUTAGE":
                modem = self.backhaul_by_profile["nb_iot"]
                modem.trigger_outage()
                yield self.env.timeout(ev['dur'])
                modem.recover_outage()
            elif ev['type'] == "5G_OUTAGE":
                modem = self.backhaul_by_profile["5g_nr"]
                modem.trigger_outage()
                yield self.env.timeout(ev['dur'])
                modem.recover_outage()

    def run_trace(self):
        for pid, p in self.registry.items():
            yield self.env.timeout(max(0, p['arr'] - self.env.now))
            self.env.process(self.process_packet(p))

    def process_packet(self, p):
        self._update_cpu_q_area()
        if len(self.cpu_q) >= self.max_cpu_q:
            self.update_status(p, "DROP_QUEUE_OVERFLOW_CPU")
            return

        p['ts_enter_cpu_q'] = self.env.now
        self.cpu_q.append(p)
        self.update_status(p, "IN_FLIGHT_CPU_Q")
        req = self.cpu.request()
        yield req

        self._update_cpu_q_area()
        self.cpu_q.remove(p)
        p['cpu_q_delay'] = self.env.now - p['ts_enter_cpu_q']
        self.update_status(p, "IN_FLIGHT_CPU_PROC")

        proc_time = 0.005
        yield self.env.timeout(proc_time)

        e_cpu = 2.0 * proc_time
        self.cpu_energy_consumed += e_cpu
        self.battery_j = max(0, self.battery_j - e_cpu)

        cpu_elap = self.env.now - p['arr']
        dl = 1.0 if p['emerg'] else 10.0

        # Candidate metrics are built through the technology-agnostic adapter
        # contract. The current simulator registers NB-IoT and 5G NR only.
        candidate_rows = []
        candidate_context = {}
        feas = []
        for candidate_index, modem in enumerate(self.backhauls):
            predicted_latency = cpu_elap + modem.estimate_delay(p['payload'])
            estimated_energy = modem.estimate_energy(p['payload'])
            candidate_rows.append([
                predicted_latency, estimated_energy, modem.rel, modem.bw
            ])
            candidate_context[candidate_index] = modem.selection_energy_context(
                p['payload'], predicted_latency
            )
            if modem.avail and predicted_latency <= dl:
                feas.append(candidate_index)

        dm = np.asarray(candidate_rows, dtype=float)

        # Preserve legacy output columns so archived analysis remains compatible.
        nb_index = next(i for i, modem in enumerate(self.backhauls) if modem.profile_id == "nb_iot")
        g5_index = next(i for i, modem in enumerate(self.backhauls) if modem.profile_id == "5g_nr")
        p['lat_nb_pred'], p['eng_nb_pred'] = dm[nb_index, 0], dm[nb_index, 1]
        p['lat_5g_pred'], p['eng_5g_pred'] = dm[g5_index, 0], dm[g5_index, 1]
        p['rel_nb'], p['rel_5g'] = dm[nb_index, 2], dm[g5_index, 2]
        p['bw_nb'], p['bw_5g'] = dm[nb_index, 3], dm[g5_index, 3]
        p['feas_nb'] = nb_index in feas
        p['feas_5g'] = g5_index in feas

        if not feas:
            self.update_status(p, "DROP_QOS")
        else:
            t0 = time.perf_counter()
            battery_pct = (self.battery_j / self.max_batt) * 100
            if callable(getattr(self.algo, "select_network_with_context", None)):
                sel = self.algo.select_network_with_context(
                    feas, dm, p['emerg'], battery_pct,
                    arrival_time_s=float(p['arr']),
                    now_s=float(self.env.now),
                    candidates=candidate_context,
                )
                decision = dict(getattr(self.algo, "last_decision", {}) or {})
                if decision:
                    p['controller_decision_mode'] = decision.get('decision_mode', '')
                    p['controller_selected_profile_id'] = decision.get('selected_profile_id', '')
                    p['controller_preferred_profile_id'] = decision.get('preferred_profile_id', '')
                    p['controller_reason'] = decision.get('reason', '')
                    p['controller_preferred_network'] = decision.get('preferred_network', -1)
                    p['controller_expected_packets_per_burst'] = decision.get('expected_packets_per_burst', float('nan'))
                    p['controller_persistent_switch'] = bool(decision.get('persistent_switch', False))
                    p['controller_packet_override'] = bool(decision.get('packet_override', False))
                    p['controller_candidate_costs_j_per_packet'] = decision.get('candidate_costs_j_per_packet', {})
                    self.decision_log.append({
                        'pid': p['pid'], 'arrival_time_s': float(p['arr']),
                        'selected_network': int(sel), **decision,
                    })
            else:
                sel = self.algo.select_network(feas, dm, p['emerg'], battery_pct)
            t1 = time.perf_counter()

            if sel == -1:
                self.update_status(p, "DROP_QOS")
                self.cpu.release(req)
                return

            p['algo_time_us'] = (t1 - t0) * 1e6
            p['ahp_state'] = self.algo.get_ahp_state(p['emerg'], (self.battery_j/self.max_batt)*100)

            if sel != self.prev_network and self.prev_network != -1: self.switches += 1
            self.prev_network = sel

            if not 0 <= int(sel) < len(self.backhauls):
                self.update_status(p, "DROP_QOS")
                self.cpu.release(req)
                return
            bh = self.backhauls[int(sel)]
            p['sel_net'] = sel
            p['lat_pred_sel'] = dm[sel, 0]
            bh.add_packet(p)

        self.cpu.release(req)

    def end_of_simulation_sweep(self):
        # Idempotent Final Classification leveraging current 'stage'
        self._update_cpu_q_area()
        for modem in self.backhauls:
            modem._update_q_area()

        valid_terminals = {"DELIVERED", "DROP_QOS", "DROP_OUTAGE", "DROP_RELIABILITY", "DROP_QUEUE_OVERFLOW_CPU", "DROP_QUEUE_OVERFLOW_BH"}
        valid_inflight = {"IN_FLIGHT_GENERATED", "IN_FLIGHT_CPU_Q", "IN_FLIGHT_CPU_PROC", "IN_FLIGHT_BH_Q", "IN_FLIGHT_TX"}

        for pid, p in self.registry.items():
            if p['status'] in valid_terminals:
                continue 

            stage = p.get('stage', 'GENERATED')
            if stage == 'GENERATED':
                self.update_status(p, "IN_FLIGHT_GENERATED")
            elif stage in valid_inflight:
                self.update_status(p, stage)
            else:
                raise ValueError(f"Unknown stage {stage} for packet {pid}")
