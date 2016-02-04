#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from nose.plugins.attrib import attr
import requests

from pyon.util.int_test import IonIntegrationTestCase

from pyon.core.governance import get_actor_header, MSG_HEADER_ACTOR, MSG_HEADER_ROLES, MSG_HEADER_VALID
from pyon.core.registry import getextends
from pyon.public import BadRequest, NotFound, IonObject, RT, PRED, OT, CFG
from ion.util.ui_utils import clear_auth, get_arg, get_auth, set_auth
from pyon.util.containers import named_any, current_time_millis

from interface.services.scion.iscion_management import ScionManagementClient
from interface.services.core.iidentity_management_service import IdentityManagementServiceClient
from interface.objects import Org, UserRole


@attr('INT', group='scion')
class TestScionManagement(IonIntegrationTestCase):
    """Test for scion_management with demo data preloaded
    """

    def setUp(self):
        self._start_container()
        self.patch_alt_cfg('scion.process.preload.preloader.CFG',
                           {'scion': {'preload': {'enabled': True}}})
        self.container.start_rel_from_url('res/deploy/scion.yml')

        self.rr = self.container.resource_registry
        self.scion_client = ScionManagementClient()
        self.idm_client = IdentityManagementServiceClient()
        self.system_actor_id = None

        self.ui_server_proc = self.container.proc_manager.procs_by_name["ui_server"]
        self.ui_base_url = self.ui_server_proc.base_url
        self.sg_base_url = self.ui_server_proc.gateway_base_url

    def tearDown(self):
        pass

    def test_scion(self):
        pass