#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.core.governance import ANONYMOUS_ACTOR
from pyon.public import log, CFG, BadRequest, EventPublisher, Conflict, Unauthorized, NotFound, PRED, OT, RT

from interface.services.scion.iscion_management import BaseScionManagement


class ScionManagementServiceBase(BaseScionManagement):

    def on_init(self):
        self.rr = self.clients.resource_registry
        self.event_repo = self.container.event_repository
        self.idm_client = self.clients.identity_management
        self.rm_client = self.clients.resource_management
        self.evt_pub = EventPublisher(process=self)

    # -------------------------------------------------------------------------

    def _get_actor_id(self):
        """Return the ion-actor-id from the context, if set and present.
        Note: may return the string 'anonymous' for an unauthenticated user"""
        ctx = self.get_context()
        ion_actor_id = ctx.get('ion-actor-id', None) if ctx else None
        return ion_actor_id

    def _actor_context(self):
        ctx = self.get_context()
        ion_actor_id = ctx.get('ion-actor-id', None) if ctx else None
        return dict(actor_id=ion_actor_id)

    def _get_actor_roles(self):
        """Return the ion-actor-roles from the context, if set and present."""
        ctx = self.get_context()
        ion_actor_roles = ctx.get('ion-actor-roles', {}) if ctx else {}
        return ion_actor_roles

    def _as_actor_id(self, actor_id=None):
        current_actor_id = self._get_actor_id()
        if current_actor_id == ANONYMOUS_ACTOR:
            current_actor_id = None
        if actor_id and not current_actor_id:
            # This may be ok for some guest calls, but is dangerous
            pass
        elif actor_id and actor_id != current_actor_id:
            # This should only be allowed for a superuser or within the same org
            pass
        return actor_id or current_actor_id

