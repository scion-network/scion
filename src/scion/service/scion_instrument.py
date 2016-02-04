#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.public import log, CFG, BadRequest, EventPublisher, Conflict, Unauthorized, AssociationQuery, NotFound, PRED, OT, ResourceQuery, RT

from scion.service.scion_base import ScionManagementServiceBase


class ScionInstrumentOps(ScionManagementServiceBase):

    def _on_init(self):
        pass

    # -------------------------------------------------------------------------

    def find_instruments(self):
        inst_objs, _ = self.rr.find_resources(RT.Instrument, id_only=False)
        return inst_objs

    # -------------------------------------------------------------------------

    def find_datasets(self):
        dataset_objs, _ = self.rr.find_resources(RT.Dataset, id_only=False)
        return dataset_objs

    # -------------------------------------------------------------------------

    def start_agent(self, asset_id='', arguments=None):
        pass

    def stop_agent(self, asset_id=''):
        pass