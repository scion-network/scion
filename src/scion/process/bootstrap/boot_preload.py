#!/usr/bin/env python

"""Bootstrap plugin"""

__author__ = 'Michael Meisinger'

from pyon.public import IonObject, RT, CFG, get_ion_ts, get_sys_name
from ion.core.bootstrap_process import BootstrapPlugin, AbortBootstrap
from scion.process.preload.preloader import ScionLoader


class BootstrapPreload(BootstrapPlugin):
    """
    Bootstrap process for calling preload
    """

    def on_initial_bootstrap(self, process, config, **kwargs):
        self.process = process
        self._do_preload()

    def on_restart(self, process, config, **kwargs):
        self.process = process
        self._do_preload()

    def _do_preload(self):
        preloader = ScionLoader()
        preloader.container = self.process.container
        preloader.process = self.process
        preloader.CFG = dict(op="auto")
        preloader.on_init()
