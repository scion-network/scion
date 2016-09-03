#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.public import log, CFG, BadRequest, EventPublisher, Conflict, Unauthorized, AssociationQuery, NotFound, \
    PRED, OT, ResourceQuery, RT, get_ion_ts, get_ion_ts_millis, dict_merge

from ion.agent.control import AgentControl, StreamingAgentClient
from scion.service.scion_base import ScionManagementServiceBase

from interface.objects import MediaResponse


class ScionInstrumentOps(ScionManagementServiceBase):

    def _on_init(self):
        pass

    # -------------------------------------------------------------------------

    def find_instruments(self):
        inst_objs, _ = self.rr.find_resources(RT.Instrument, id_only=False)
        # Find agent processes and match up
        agent_entries = self.container.directory.find_child_entries("/Agents", direct_only=True)
        active_agents_iids = {}
        for agent_entry in agent_entries:
            agent_name = agent_entry.attributes.get("name", "")
            resource_id = agent_entry.attributes.get("resource_id", "")
            if agent_name.startswith("data_agent_") and resource_id:
                active_agents_iids[resource_id] = agent_entry.key
        for inst in inst_objs:
            inst.addl["agent_active"] = bool(inst._id in active_agents_iids)
            inst.addl["agent_pid"] = active_agents_iids.get(inst._id, "")
        return inst_objs

    # -------------------------------------------------------------------------

    def find_datasets(self):
        dataset_objs, _ = self.rr.find_resources(RT.Dataset, id_only=False)
        return dataset_objs

    def get_asset_data(self, asset_id='', data_format='', data_filter=None):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        dataset_objs, _ = self.rr.find_objects(asset_id, PRED.hasDataset, RT.Dataset, id_only=False)
        if not dataset_objs:
            raise BadRequest("Could not find dataset")
        dataset_obj = dataset_objs[0]

        from ion.data.persist.hdf5_dataset import DatasetHDF5Persistence
        persistence = DatasetHDF5Persistence(dataset_obj._id, dataset_obj.schema_definition, "hdf5")
        data_filter1 = dict(transpose_time=True, time_format="unix_millis", max_rows=1000)
        data_filter1.update(data_filter or {})

        data_info = dict(dataset_id=dataset_obj._id, ts_generated=get_ion_ts(),
                         data={}, info={}, num_rows=0)

        if data_filter1.get("get_info", None) is True:
            data_info["variables"] = [var_info["name"] for var_info in dataset_obj.schema_definition["variables"]]
            data_info["schema"] = dataset_obj.schema_definition
            res_info = persistence.get_data_info(data_filter1)
            data_info["info"].update(res_info)

        if data_filter1.get("include_data", True):
            raw_data = persistence.get_data(data_filter=data_filter1)
            data_info["data"] = raw_data
            data_info["num_rows"] = len(raw_data.values()[0]) if raw_data else 0

        return data_info

    def download_asset_data(self, asset_id='', data_format='', data_filter=None):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        dataset_objs, _ = self.rr.find_objects(asset_id, PRED.hasDataset, RT.Dataset, id_only=False)
        if not dataset_objs:
            raise BadRequest("Could not find dataset")
        dataset_obj = dataset_objs[0]

        if data_format and data_format != "hdf5":
            raise BadRequest("Unsupported download data format")

        from ion.data.persist.hdf5_dataset import DatasetHDF5Persistence
        persistence = DatasetHDF5Persistence(dataset_obj._id, dataset_obj.schema_definition, "hdf5")
        data_filter1 = dict(transpose_time=True, time_format="unix_millis", max_rows=100000,
                            start_time=get_ion_ts_millis() - 86400000)
        data_filter1.update(data_filter or {})
        temp_filename = persistence.get_data_copy(data_filter=data_filter1)

        resp_hdrs = {"Content-Disposition": 'attachment; filename="ds_%s.hdf5"' % asset_obj._id}

        mr = MediaResponse(media_mimetype="application/octet-stream", body=temp_filename,
                           internal_encoding="filename", response_headers=resp_hdrs)

        return mr


    # -------------------------------------------------------------------------

    def start_agent(self, asset_id='', arguments=None):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        if not asset_obj.agent_info:
            raise BadRequest("Cannot find agent information")

        agent_info = asset_obj.agent_info[0]
        agent_cfg = agent_info.get("config") or {}
        if arguments and type(arguments) is dict:
            dict_merge(agent_cfg, arguments, inplace=True)

        dataset_info = self.get_asset_data(asset_id, data_filter=dict(get_info=True, include_data=False))
        dataset_id = dataset_info["dataset_id"]
        agent_cfg["dataset_id"] = dataset_id
        agent_cfg["dataset_info"] = {}
        log.info("Start agent for %s with dataset %s", asset_id, dataset_id)
        if dataset_info and dataset_info["info"]:
            log.info("Agent RESTART %s. Dataset exists, last sample date: %s", asset_id, dataset_info["info"]["ts_last_str"])
            agent_cfg["dataset_info"] = dataset_info["info"]
        log.info("Using agent_info: %s", agent_info)
        agent_ctl = AgentControl()
        agent_pid = agent_ctl.launch_agent(asset_id, agent_info["agent_type"], agent_cfg)

        asset_obj.agent_state = {}  # We assume only 1 agent per asset
        asset_obj.agent_state[agent_pid] = dict(start_ts=get_ion_ts())
        self.rr.update(asset_obj)

        log.info("Agent started for %s with pid=%s", asset_id, agent_pid)

        return agent_pid

    def stop_agent(self, asset_id=''):
        asset_obj = self._validate_resource_id("asset_id", asset_id, RT.Instrument)
        log.info("Stop agent for %s", asset_id)
        try:
            agent_ctl = AgentControl(resource_id=asset_id)
            agent_ctl.terminate_agent()

        finally:
            if StreamingAgentClient.is_agent_active(asset_id):
                log.warn("Removing agent directory entry for %s", asset_id)
            proc_id = StreamingAgentClient._get_agent_process_id(asset_id)
            self.container.directory.unregister_safe("/Agents", proc_id)

            asset_obj.agent_state = {}
            self.rr.update(asset_obj)
