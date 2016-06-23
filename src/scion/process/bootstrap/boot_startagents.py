#!/usr/bin/env python

"""Bootstrap plugin"""

__author__ = 'Michael Meisinger'

from pyon.public import IonObject, RT, CFG, get_ion_ts, get_sys_name, log
from ion.core.bootstrap_process import BootstrapPlugin, AbortBootstrap
from scion.process.preload.preloader import ScionLoader

from interface.services.scion.iscion_management import ScionManagementProcessClient


class BootstrapStartAgents(BootstrapPlugin):
    """
    Bootstrap process for calling preload
    """

    def on_initial_bootstrap(self, process, config, **kwargs):
        self.process = process

    def on_restart(self, process, config, **kwargs):
        self.process = process
        inst_objs, _ = process.container.resource_registry.find_resources(restype=RT.Instrument, id_only=False)
        active_agents = []
        for inst in inst_objs:
            if len(inst.agent_state) >= 1:
                active_agents.append(inst._id)

        if not active_agents:
            return

        log.info("Restarting %s agents: %s", len(active_agents), active_agents)

        svc_client = ScionManagementProcessClient(process=process)
        for inst_id in active_agents:
            try:
                svc_client.start_agent(inst_id)
            except Exception:
                log.exception("Cannot restart agent for %s" % inst_id)
