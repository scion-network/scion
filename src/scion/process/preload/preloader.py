#!/usr/bin/env python

__author__ = 'Michael Meisinger'

import base64
import os

from pyon.ion.resource import create_access_args
from pyon.public import ImmediateProcess, CFG, log, OT, PRED, RT, IonObject, get_ion_ts, BadRequest, NotFound, get_sys_name, dict_merge
from pyon.ion.identifier import create_unique_resource_id, create_unique_association_id
from ion.util.preload import Preloader, KEY_ID

from ion.data.schema.schema import DataSchemaParser

from interface.services.core.iidentity_management_service import IdentityManagementServiceProcessClient, IdentityManagementServiceClient
from interface.services.core.iorg_management_service import OrgManagementServiceProcessClient, OrgManagementServiceClient
from interface.services.scion.iscion_management import ScionManagementProcessClient


class ScionLoader(ImmediateProcess, Preloader):

    def on_init(self):
        self.process = getattr(self, "process", None) or self

        self.rr = self.container.resource_registry
        self.idm_client = IdentityManagementServiceProcessClient(process=self.process)
        self.org_client = OrgManagementServiceProcessClient(process=self.process)
        self.scion_client = ScionManagementProcessClient(process=self.process)

        self.op = self.CFG.get("op", "load")

        if self.op == "auto":
            self.do_auto_preload()
        elif self.op == "load":
            preload_master = CFG.get_safe("scion.preload.default_master")
            if preload_master:
                self.do_preload_master(preload_master)
        else:
            raise BadRequest("Unknown command")

    def do_preload_core(self):
        client_obj = IonObject(RT.ActorIdentity, name="SciON UI Client",
                               details=IonObject(OT.OAuthClientIdentityDetails, default_scopes="scion"))
        client_actor_id = self.idm_client.create_actor_identity(client_obj)
        client_id = "client:scion_ui"
        self.idm_client.set_actor_credentials(client_actor_id, client_id, "client_secret")
        return True

    def do_auto_preload(self):
        """ Load configured preload scenarios and remembers in directory which ones
        have been loaded. """
        log.info("Executing auto preload")
        preload_entries = self.process.container.directory.lookup("/System/Preload")
        preload_changed = False
        if preload_entries is None:
            preload_entries = dict(scenarios={})
            preload_changed = True

        # "HACK" Preload core to get app specifics in
        if "core" not in preload_entries["scenarios"]:
            preload_entries["scenarios"]["core"] = self._get_dir_entry("core")
            self.do_preload_core()
            preload_changed = True

        preload_scenarios = CFG.get_safe("scion.preload.scenarios")
        preload_scope = CFG.get_safe("scion.preload.scope")
        for scenario_info in preload_scenarios:
            scope, scenario = scenario_info
            if scope == "all" or scope == preload_scope:
                if scenario not in preload_entries["scenarios"]:
                    preload_entries["scenarios"][scenario] = self._get_dir_entry(scenario)
                    changed = self.do_preload_master(scenario)
                    preload_changed = preload_changed or changed

        if preload_changed:
            self.process.container.directory.register("/System", "Preload", scenarios=preload_entries["scenarios"])

    def _get_dir_entry(self, scenario):
        return dict(ts=get_ion_ts(), name=scenario, sys_name=get_sys_name())

    def do_preload_master(self, master):
        if CFG.get_safe("scion.preload.enabled", False) is not True:
            return False
        log.info("############## PRELOAD SCION RESOURCES (%s) ##############", master)

        skip_steps = CFG.get_safe("skipsteps")
        if skip_steps:
            skip_steps = skip_steps.split(",")
        self.initialize_preloader(self.process, {})

        if os.path.isdir("res/preload/{}".format(master)):
            self.preload_master("res/preload/{}/actions.yml".format(master), skip_steps=skip_steps)
        elif os.path.exists("res/preload/{}".format(master)):
            self.preload_master("res/preload/{}".format(master), skip_steps=skip_steps)
        else:
            raise BadRequest("Cannot find preload master")

        log.info("############## END PRELOAD ##############")
        return True


    # -------------------------------------------------------------------------
    # Action callbacks

    def _load_preload_CommitBulk(self, action_cfg):
        self.commit_bulk()

    def _load_resource_CORE_CreateRole(self, action_cfg):
        org_name = action_cfg["org"]
        role_name = action_cfg["role"]
        org_obj = self.org_client.find_org(org_name)
        role_obj = IonObject(RT.UserRole, name=role_name, governance_name=role_name,
                             description="Role %s.%s" % (org_name, role_name))

        self.org_client.add_org_role(org_obj._id, role_obj, headers=self._get_system_actor_headers())

    def _load_resource_APP_ScionUser(self, action_cfg):
        actor_obj = self.create_object_from_cfg(action_cfg, RT.ActorIdentity)
        username, password = action_cfg["username"], action_cfg.get("password", None)
        user_alias = action_cfg[KEY_ID]
        if user_alias in self.resource_ids:
            log.info("Skipping existing user '%s', alias=%s", username, user_alias)
            return
        log.debug("Preload user '%s', alias=%s", username, user_alias)

        actor_id = self.scion_client.define_user(
                first_name=actor_obj.details.contact.individual_names_given,
                last_name=actor_obj.details.contact.individual_name_family,
                username=username, password=password, email=actor_obj.details.contact.email,
                attributes=actor_obj.details.profile)
        self.scion_client.update_user_contact(actor_id, actor_obj.details.contact)

        res_obj = self.container.resource_registry.read(actor_id)
        res_obj.alt_ids += ['PRE:'+action_cfg[KEY_ID]]
        self.container.resource_registry.update(res_obj)
        self._register_id(action_cfg[KEY_ID], actor_id, res_obj)

        # Roles
        roles = action_cfg.get("roles", [])
        for role in roles:
            org_name, role_name = role.split(".", 1)
            org_obj = self.org_client.find_org(org_name)
            self.org_client.grant_role(org_obj._id, actor_id, role_name, headers=self._get_system_actor_headers())

    def _load_resource_Instrument(self, action_cfg):
        if action_cfg[KEY_ID] in self.resource_ids:
            return
        res_id = self.basic_resource_create(action_cfg, RT.Instrument, "resource_registry", "create", support_bulk=True)
        self.basic_associations_create(action_cfg, action_cfg[KEY_ID], support_bulk=True)

    def _load_resource_Dataset(self, action_cfg):
        if action_cfg[KEY_ID] in self.resource_ids:
            return
        schema_def = {}
        if "schema_def" in action_cfg:
            schema_def = DataSchemaParser.parse_schema_ref(action_cfg["schema_def"])
        if "schema_override" in action_cfg:
            dict_merge(schema_def, action_cfg["schema_override"], inplace=True)
        res_id = self.basic_resource_create(action_cfg, RT.Dataset, "resource_registry", "create", support_bulk=True,
                                            set_attributes=dict(schema_definition=schema_def))
        self.basic_associations_create(action_cfg, action_cfg[KEY_ID], support_bulk=True)

    def _load_action_StartAgent(self, action_cfg):
        asset_id = action_cfg["asset_id"]
        agent_res_id = self.resource_ids[asset_id]
        self.scion_client.start_agent(agent_res_id)