#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.core.governance import get_system_actor_header
from pyon.ion.resource import create_access_args
from pyon.public import log, Container, PRED, RT, OT, ResourceQuery, AssociationQuery
from ion.process.ui.admin_ui import build_command, build_link, get_rr_access_args, get_arg, _link

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
        fragments.append(build_command("Run preload scenario", "/cmd/sys_run_preload"))
        fragments.append(build_command("Create user", "/cmd/sys_create_user"))

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

    def _process_cmd_sys_run_preload(self, resource_id, res_obj=None):
        fragments = []
        if get_arg("scenario"):
            scenario = get_arg("scenario")
            if scenario:
                from scion.process.preload.preloader import ScionLoader
                preloader = ScionLoader()
                preloader.container = Container.instance
                preloader.process = self.adminui
                preloader.CFG = dict(op="load", agprox=dict(preload_master=scenario))
                preloader.on_init()
                fragments.append("Preload scenario '%s' executed.<br>OK" % scenario)
            else:
                fragments.append("Invalid arguments for scenario.")

        else:
            fragments.append("</pre><h2>Run Preload Scenario</h2>")
            fragments.append("<form id='form_run_preload' action='%s' method='post'>" % _link('/cmd/sys_run_preload'))
            fragments.append("Scenario: <input name='scenario'><br>")
            fragments.append("<input name='submit' type='submit' value='Run'><br>")
            fragments.append("</form>")
            fragments.append("<pre>")

        msg_text = "".join(fragments)
        return msg_text

    def _process_cmd_sys_create_user(self, resource_id, res_obj=None):
        fragments = []
        if get_arg("email"):
            first, last, email, password = get_arg("first_name"), get_arg("last_name"), get_arg("email"), get_arg(
                "password")
            if first and last and email and password:
                sys_headers = get_system_actor_header()
                self.scion_client.define_user(None, first, last, email, password, email=email, headers=sys_headers)
                fragments.append("User '%s' created.<br>OK" % email)
            else:
                fragments.append("Invalid arguments to create user.")

        else:
            fragments.append("</pre><h2>Create User</h2>")
            fragments.append("<form id='form_user_create' action='%s' method='post'>" % _link('/cmd/sys_create_user'))
            fragments.append("First name: <input name='first_name'><br>")
            fragments.append("Last name: <input name='last_name'><br>")
            fragments.append("Email: <input name='email' type='email'><br>")
            fragments.append("Password: <input name='password' type='password'><br><br>")
            fragments.append("<input name='submit' type='submit' value='Create'><br>")
            fragments.append("</form>")
            fragments.append("<pre>")

        msg_text = "".join(fragments)
        return msg_text
