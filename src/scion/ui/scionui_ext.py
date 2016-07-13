#!/usr/bin/env python

__author__ = 'Michael Meisinger'

import flask
from flask import Blueprint, request, render_template, redirect
import os

from pyon.core.governance import find_roles_by_actor
from pyon.public import log, CFG
from ion.util.ui_utils import UIExtension


UI_CFG_PREFIX = "scion.ui"

base_path = os.path.abspath(os.path.curdir)
static_dir = CFG.get_safe(UI_CFG_PREFIX + ".content.static") or ""
static_dir = static_dir if os.path.isabs(static_dir) else os.path.join(base_path, static_dir)
templates_dir = CFG.get_safe(UI_CFG_PREFIX + ".content.templates") or ""
templates_dir = templates_dir if os.path.isabs(templates_dir) else os.path.join(base_path, templates_dir)

ui_instance = None


class ScionUIExtension(UIExtension):
    """
    Scion UI extension.
    """
    def on_init(self, ui_server, flask_app):
        # Retain a pointer to this object for use in routes
        global ui_instance
        ui_instance = self

        log.info("Started SciON UI extension")

    def extend_user_session_attributes(self, session, actor_obj):
        actor_id = actor_obj._id
        roles = find_roles_by_actor(actor_id)  # dict with org gov names to list of role gov names
        role_list = ["%s.%s" % (on, rn) for (on, rl) in roles.iteritems() for rn in rl]
        session["auth_roles"] = sorted(role_list)
