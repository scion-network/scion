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

from orb_sources import sources


@attr('INT', group='scion')
class TestScionOrbAgentData(IonIntegrationTestCase):
    """Test for Scion with agents and data streaming
    """

    def setUp(self):
        self._start_container()
        self.patch_alt_cfg('scion.process.preload.preloader.CFG',
                           {'scion': {'preload': {'enabled': False}}})
        gevent.wait(1)  # Avoid address in use error
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

        inst_ids = []
        ds_ids = []
        for source in sources:
   
          # Instrument
          agent_info=[dict(agent_type="data_agent",
            config=dict(plugin="scion.agent.model.orb.orb_plugin.Orb_DataAgentPlugin",
            sampling_interval=0.5, stream_name="basic_streams", auto_streaming=False))]
          inst_obj = Instrument(name=source, description="Multiplexed generic compressed data frame packet",
            location=GeospatialLocation(latitude=42.867079, longitude=-127.257324), agent_info=agent_info)
          inst_id, _ = self.rr.create(inst_obj, actor_id=actor_id)
          inst_ids.append(inst_id)

          # Dataset
          schema_def = DataSchemaParser.parse_schema_ref("ds_orb_mgenc_m40")
          ds_obj = Dataset(name=source, schema_definition=schema_def)
          ds_id, _ = self.rr.create(ds_obj, actor_id=actor_id)
          self.rr.create_association(inst_id, PRED.hasDataset, ds_id)

          ds_filename = self.container.file_system.get("%s/%s%s.hdf5" % (DS_BASE_PATH, DS_FILE_PREFIX, ds_id))
          self.assertFalse(os.path.exists(ds_filename))

          inst_data_t0 = self.scion_client.get_asset_data(inst_id)
          self.assertEquals(inst_data_t0["dataset_id"], ds_id)
          self.assertEquals(inst_data_t0["num_rows"], 0)
          ds_ids.append(ds_id)

        # Install a data packet catcher
        # TODO

        # Start agent
        sacs = []
        for idx, source in enumerate(sources):
          self.assertFalse(StreamingAgentClient.is_agent_active(inst_ids[idx]))
          agent_pid = self.scion_client.start_agent(inst_ids[idx])
          self.assertTrue(StreamingAgentClient.is_agent_active(inst_ids[idx]))

          sac = StreamingAgentClient(resource_id=inst_ids[idx], process=self.scion_proc)
          agent_status = sac.get_status()
          self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_INITIALIZED)

          sac.connect()
          agent_status = sac.get_status()
          self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_CONNECTED)

          # Coming in from the agent config.
          streaming_args = { 
              #'orb_name' : 'taexport.ucsd.edu:usarrayTA',
              'orb_name' : 'ceusnexport.ucsd.edu:usarray',
              'select' : source,
              '--timeout' : 5,
              'sample_interval' : 5 
          }

          sac.start_streaming(streaming_args)
          agent_status = sac.get_status()
          self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_STREAMING)
          sacs.append(sac)

        gevent.sleep(120)

        # Take down agent
        for idx, sac in enumerate(sacs):
          #sac.stop_streaming()  # Not required to stop agent, just to test here
          #agent_status = sac.get_status()
          #self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_CONNECTED)

          #sac.disconnect()
          #agent_status = sac.get_status()
          #self.assertEquals(agent_status["current_state"], StreamingAgent.AGENTSTATE_INITIALIZED)

          self.scion_client.stop_agent(inst_ids[idx])
          self.assertFalse(StreamingAgentClient.is_agent_active(inst_ids[idx]))
        


