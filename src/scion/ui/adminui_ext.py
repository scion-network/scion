#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.ion.resource import create_access_args
from pyon.public import log, Container, PRED, RT, OT, ResourceQuery, AssociationQuery
from ion.process.ui.admin_ui import build_command, build_link, get_rr_access_args

from interface.services.scion.iscion_management import ScionManagementProcessClient

class AdminUIExtension(object):

    def __init__(self, app, adminui):
        log.info("Initialized AdminUI extension for SciON")
        self.app = app
        self.adminui = adminui
        self.rr = Container.instance.resource_registry
        self.scion_client = ScionManagementProcessClient(process=self.adminui)

    def system_commands(self, fragments):
        fragments.append(build_command("Reload access policy", "/cmd/sys_reload_policy"))

    def resource_commands(self, resource_id, restype, fragments):
        if restype == "Instrument":
            fragments.append(build_command("Start agent", "/cmd/start_agent?rid=%s" % resource_id))
            fragments.append(build_command("Stop agent", "/cmd/stop_agent?rid=%s" % resource_id))

    # -------------------------------------------------------------------------

    def _process_cmd_start_agent(self, resource_id, res_obj=None):
        msg_lines = []
        res = self.scion_client.start_agent(resource_id)

        msg_text = "<br>".join(msg_lines) + "<br><br>"

        return "%sOK. Started agent for %s '%s'<br><br>" % (msg_text, res_obj.type_, resource_id)

    def _process_cmd_stop_agent(self, resource_id, res_obj=None):
        msg_lines = []
        res = self.scion_client.stop_agent(resource_id)

        msg_text = "<br>".join(msg_lines) + "<br><br>"

        return "%sOK. Stopped agent for %s '%s'<br><br>" % (msg_text, res_obj.type_, resource_id)

    # -------------------------------------------------------------------------

    def _process_cmd_sys_reload_policy(self, resource_id, res_obj=None):
        policy_ids, _ = self.rr.find_resources(RT.Policy, id_only=True)
        for pol_id in policy_ids:
            self.rr.delete(pol_id)

        from ion.process.bootstrap.load_system_policy import LoadSystemPolicy
        LoadSystemPolicy.op_load_system_policies(self.adminui)

        new_policy_ids, _ = self.rr.find_resources(RT.Policy, id_only=True)

        msg_text = "Deleted %s policies.<br>Added %s new policies.<br><br>OK." % (len(policy_ids), len(new_policy_ids))

        return msg_text
