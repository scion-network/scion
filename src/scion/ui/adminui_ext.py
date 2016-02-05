#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.ion.resource import create_access_args
from pyon.public import log, Container, PRED, RT, OT, ResourceQuery, AssociationQuery
from ion.processes.ui.admin_ui import build_command, build_link, get_rr_access_args


class AdminUIExtension(object):

    def __init__(self, app, adminui):
        log.info("Initialized AdminUI extension for SciON")
        self.app = app
        self.adminui = adminui
        self.rr = Container.instance.resource_registry

    def system_commands(self, fragments):
        fragments.append(build_command("Reload access policy", "/cmd/sys_reload_policy"))

    def resource_commands(self, resource_id, restype, fragments):
        pass

    def _process_cmd_sys_reload_policy(self, resource_id, res_obj=None):
        policy_ids, _ = self.rr.find_resources(RT.Policy, id_only=True)
        for pol_id in policy_ids:
            self.rr.delete(pol_id)

        from ion.processes.bootstrap.load_system_policy import LoadSystemPolicy
        LoadSystemPolicy.op_load_system_policies(self.adminui)

        new_policy_ids, _ = self.rr.find_resources(RT.Policy, id_only=True)

        msg_text = "Deleted %s policies.<br>Added %s new policies.<br><br>OK." % (len(policy_ids), len(new_policy_ids))

        return msg_text
