#!/usr/bin/env python

__author__ = 'Edward Hunter'

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
class TestScionCDIPAgentData(IonIntegrationTestCase):
    """Test for Scion with agents streaming data from CDIP source
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
                         config=dict(plugin="scion.agent.model.cdip.cdip_plugin.CDIP_DataAgentPlugin",
                                     sampling_interval=10, stream_name="basic_streams",
                                     auto_streaming=False))]
        inst_obj = Instrument(name="TA_121A/MGENC/M40", description="CDIP buoy data",
                              location=GeospatialLocation(latitude=37.94831666666667, longitude=-123.4675),
                              agent_info=agent_info)
        inst_id, _ = self.rr.create(inst_obj, actor_id=actor_id)

        # Create dataset
        schema_def = DataSchemaParser.parse_schema_ref("ds_cdip01_main")
        ds_obj = Dataset(name="Dataset Sensor",
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
            #log.info('Packet data: ' + str(packet.data))
        def cleanup_stream_sub():
            if self.stream_sub:
                self.stream_sub.stop()
                self.stream_sub = None

        self.stream_sub = StreamSubscriber(process=self.scion_proc, stream="basic_streams", callback=process_packet_cb)
        self.stream_sub.start()
        
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

        # Coming in from the agent config.
        streaming_args = { 
            'url' : 'http://cdip.ucsd.edu/data_access/justdar.cdip?029+pm',
            'sampling_interval' : 10
        }

        sac.start_streaming(streaming_args)
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_STREAMING)

        # Set to progressively high values for real data stream tests.
        gevent.sleep(20)

        # Retrieve data
        self.assertTrue(os.path.exists(ds_filename))

        inst_data = self.scion_client.get_asset_data(inst_id)
        """
        {'data': {'Dp': [[1465682100000, 325]],
            'Hs': [[1465682100000, 3.03]],
            'Ta': [[1465682100000, 6.92]],
            'Temp': [[1465682100000, 12.2]],
            'Tp': [[1465682100000, 9.09]]},
         'dataset_id': '08bc829159e6401182462b713b180dbe',
         'num_rows': 1,
         'ts_generated': '1465685467675',
         'var_def': [{'base_type': 'ntp_time',
              'description': 'NTPv4 timestamp',
              'name': 'time',
              'storage_dtype': 'i8',
              'unit': ''},
             {'base_type': 'float',
              'description': 'Significant wave height',
              'name': 'Hs',
              'storage_dtype': 'f8',
              'unit': 'meters'},
             {'base_type': 'float',
              'description': 'Peak wave period',
              'name': 'Tp',
              'storage_dtype': 'f8',
              'unit': 'seconds'},
             {'base_type': 'int',
              'description': 'Peak wave direction',
              'name': 'Dp',
              'storage_dtype': 'i4',
              'unit': 'degrees'},
             {'base_type': 'float',
              'description': 'Average wave period',
              'name': 'Ta',
              'storage_dtype': 'f8',
              'unit': 'seconds'},
             {'base_type': 'float',
              'description': 'Surface temperature',
              'name': 'Temp',
              'storage_dtype': 'f8',
              'unit': 'celcius'}],
         'variables': ['time', 'Hs', 'Tp', 'Dp', 'Ta', 'Temp']}
        """
        num_rows = inst_data["num_rows"]
        log.info('CDIP test produced %i data rows.' % num_rows)

        # Take down agent
        sac.stop_streaming()  # Not required to stop agent, just to test here
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_CONNECTED)

        sac.disconnect()
        agent_status = sac.get_status()
        self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_INITIALIZED)

        self.scion_client.stop_agent(inst_id)

        self.assertFalse(StreamingAgentClient.is_agent_active(inst_id))
        

