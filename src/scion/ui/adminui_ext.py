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
        pass

    def resource_commands(self, resource_id, restype, fragments):
        pass
