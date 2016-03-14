#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from nose.plugins.attrib import attr
import gevent
import os

from pyon.util.int_test import IonIntegrationTestCase
from pyon.public import BadRequest, NotFound, IonObject, RT, PRED, OT, CFG, StreamSubscriber, log

from ion.agent.control import AgentControl, StreamingAgentClient
from ion.agent.streaming_agent import StreamingAgent
from ion.data.persist.hdf5_dataset import DS_BASE_PATH, DS_FILE_PREFIX
from ion.data.schema.schema import DataSchemaParser

from interface.services.scion.iscion_management import ScionManagementClient
from interface.services.core.iidentity_management_service import IdentityManagementServiceClient
from interface.objects import Instrument, Dataset, GeospatialLocation, DataPacket


@attr('INT', group='scion')
class TestScionAgentData(IonIntegrationTestCase):
    """Test for Scion with agents and data streaming
    """

    def setUp(self):
        self._start_container()
        self.patch_alt_cfg('scion.process.preload.preloader.CFG',
                           {'scion': {'preload': {'enabled': False}}})
        self.container.start_rel_from_url('res/deploy/scion.yml')

        self.rr = self.container.resource_registry
        self.scion_client = ScionManagementClient()
        self.idm_client = IdentityManagementServiceClient()
        self.system_actor_id = None

        self.ui_server_proc = self.container.proc_manager.procs_by_name["ui_server"]
        self.scion_proc = self.container.proc_manager.procs_by_name["scion_management"]
        self.ui_base_url = self.ui_server_proc.base_url
        self.sg_base_url = self.ui_server_proc.gateway_base_url

    def tearDown(self):
        pass

    def test_scion_agent(self):
        # Create user
        actor_id = self.scion_client.define_user(
                first_name="John", last_name="Doe",
                username="jdoe@scion.com", password="s3cret", email="jdoe@scion.com")

        # Create instrument
        agent_info=[dict(agent_type="data_agent",
                         config=dict(plugin="scion.agent.model.vmmon.vmmon_plugin.VMMON_DataAgentPlugin",
                                     sampling_interval=0.5, stream_name="basic_streams",
                                     auto_streaming=False))]
        inst_obj = Instrument(name="Sensor 1", description="CPU monitor",
                              location=GeospatialLocation(latitude=32.867079, longitude=-117.257324),
                              agent_info=agent_info)
        inst_id, _ = self.rr.create(inst_obj, actor_id=actor_id)

        # Create dataset
        schema_def = DataSchemaParser.parse_schema_ref("ds_vmmon_main")
        ds_obj = Dataset(name="Dataset Sensor 1",
                         schema_definition=schema_def)
        ds_id, _ = self.rr.create(ds_obj, actor_id=actor_id)

        self.rr.create_association(inst_id, PRED.hasDataset, ds_id)

        ds_filename = self.container.file_system.get("%s/%s%s.hdf5" % (DS_BASE_PATH, DS_FILE_PREFIX, ds_id))
        self.assertFalse(os.path.exists(ds_filename))

        inst_data_t0 = self.scion_client.get_asset_data(inst_id)
        self.assertEquals(inst_data_t0["dataset_id"], ds_id)
        self.assertEquals(inst_data_t0["num_rows"], 0)

        # Install a data packet catcher
        self.recv_packets, self.recv_rows = [], 0
        def process_packet_cb(packet, route, stream):
            if not isinstance(packet, DataPacket):
                log.warn("Received a non DataPacket message")
            self.recv_packets.append(packet)
            self.recv_rows += len(packet.data["data"])
            log.info("Received data packet #%s: rows=%s, cols=%s", len(self.recv_packets), len(packet.data["data"]),
                     packet.data["cols"])
        self.stream_sub = StreamSubscriber(process=self.scion_proc, stream="basic_streams", callback=process_packet_cb)
        self.stream_sub.start()

        def cleanup_stream_sub():
            if self.stream_sub:
                self.stream_sub.stop()
                self.stream_sub = None

        self.addCleanup(cleanup_stream_sub)

        # Start agent
        self.assertFalse(StreamingAgentClient.is_agent_active(inst_id))

        agent_pid = self.scion_client.start_agent(inst_id)

        self.assertTrue(StreamingAgentClient.is_agent_active(inst_id))

        sac = StreamingAgentClient(resource_id=inst_id, process=self.scion_proc)
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_INITIALIZED)

        sac.connect()
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_CONNECTED)

        sac.start_streaming()
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_STREAMING)

        # Retrieve data
        gevent.sleep(1)
        self.assertTrue(os.path.exists(ds_filename))

        inst_data_t1 = self.scion_client.get_asset_data(inst_id)
        self.assertEquals(inst_data_t1["dataset_id"], ds_id)
        self.assertEquals(inst_data_t1["variables"], ['time', 'cpu_percent'])
        self.assertIn("cpu_percent", inst_data_t1["data"])
        num_rows_t1 = inst_data_t1["num_rows"]
        self.assertGreaterEqual(num_rows_t1, 2)

        gevent.sleep(1)
        inst_data_t2 = self.scion_client.get_asset_data(inst_id)
        num_rows_t2 = inst_data_t2["num_rows"]
        self.assertGreater(num_rows_t2, num_rows_t1)

        self.assertGreaterEqual(len(self.recv_packets), self.recv_rows)
        self.assertLessEqual(abs(self.recv_rows - num_rows_t2), 2)

        self.scion_client.stop_agent(inst_id)

        self.assertFalse(StreamingAgentClient.is_agent_active(inst_id))
