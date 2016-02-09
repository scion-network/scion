#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.public import log, CFG, BadRequest, EventPublisher, Conflict, Unauthorized, AssociationQuery, NotFound, PRED, OT, ResourceQuery, RT

from ion.agent.control import AgentControl
from scion.service.scion_base import ScionManagementServiceBase


class ScionInstrumentOps(ScionManagementServiceBase):

    def _on_init(self):
        pass

    # -------------------------------------------------------------------------

    def find_instruments(self):
        inst_objs, _ = self.rr.find_resources(RT.Instrument, id_only=False)
        return inst_objs

    # -------------------------------------------------------------------------

    def find_datasets(self):
        dataset_objs, _ = self.rr.find_resources(RT.Dataset, id_only=False)
        return dataset_objs

    # -------------------------------------------------------------------------

    def start_agent(self, asset_id='', arguments=None):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        if not asset_obj.agent_info:
            raise BadRequest("Cannot find agent information")

        log.info("Start agent for %s", asset_id)
        agent_info = asset_obj.agent_info[0]
        log.info("Using agent_info: %s", agent_info)
        agent_ctl = AgentControl()
        agent_pid = agent_ctl.launch_agent(asset_id, agent_info["agent_type"], agent_info.get("config") or {})

        log.info("Agent started for %s with pid=%s", asset_id, agent_pid)

        return agent_pid

    def stop_agent(self, asset_id=''):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        log.info("Stop agent for %s", asset_id)
        agent_ctl = AgentControl(resource_id=asset_id)
        agent_ctl.terminate_agent()
