#!/usr/bin/env python

__author__ = 'Michael Meisinger'

from pyon.public import log, CFG, BadRequest, EventPublisher, Conflict, Unauthorized, AssociationQuery, NotFound, PRED, OT, ResourceQuery, RT
from pyon.util.containers import is_valid_identifier, parse_ion_ts, BASIC_VALID

from ion.service.identity_management_service import IdentityUtils

from scion.service.scion_base import ScionManagementServiceBase
from scion.service.scion_instrument import ScionInstrumentOps

from interface.objects import ActorIdentity, UserIdentityDetails, Credentials, ContactInformation
from interface.objects import MediaResponse, ResourceVisibilityEnum


EMAIL_VALID = BASIC_VALID + "@.-"


class ScionManagementService(ScionInstrumentOps):

    def on_init(self):
        log.info("SciON Management service starting")
        ScionManagementServiceBase.on_init(self)

        # Initialize helpers
        ScionInstrumentOps._on_init(self)


    # -------------------------------------------------------------------------

    def read_user(self, user_id=''):
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)
        user_obj.credentials = None

        return user_obj

    def register_user(self, first_name='', last_name='', username='', password='', email=''):
        return self.define_user(first_name=first_name, last_name=last_name, username=username,
                                password=password, email=email)

    def define_user(self, user_id='', first_name='', last_name='', username='', password='',
                    email='', attributes=None):
        if user_id:
            raise NotImplementedError("Update not supported: user_id=%s" % user_id)
        if not email:
            raise BadRequest('Email is required')
        username = username or email

        user = self._get_user_by_email(email)
        if user:
            raise BadRequest("Email already taken")

        if not username or not is_valid_identifier(username, valid_chars=EMAIL_VALID):
            raise BadRequest("Argument username invalid: %s" % username)
        if attributes and type(attributes) is not dict:
            raise BadRequest("Argument attributes invalid type")
        if not first_name:
            first_name = username
        attributes = attributes or {}

        full_name = ("%s %s" % (first_name, last_name)) if last_name else first_name

        IdentityUtils.check_password_policy(password)

        contact = ContactInformation(individual_names_given=first_name, individual_name_family=last_name, email=email)
        user_profile = UserIdentityDetails(contact=contact, profile=attributes)
        actor_obj = ActorIdentity(name=full_name, details=user_profile)

        # Support fast setting of credentials without expensive compute of bcrypt hash, for quick preload
        pwd_salt, pwd_hash = None, None
        if attributes and "scion_init_pwdsalt" in attributes and "scion_init_pwdhash" in attributes:
            pwd_salt, pwd_hash = attributes.pop("scion_init_pwdsalt"), attributes.pop("scion_init_pwdhash")

        user_exists = self.idm_client.is_user_existing(username)
        if user_exists:
            raise BadRequest("Username already taken")

        actor_id = self.idm_client.create_actor_identity(actor_obj)

        if pwd_salt and pwd_hash:
            # Add to credentials
            actor_obj1 = self.rr.read(actor_id)
            cred_obj = None
            for cred in actor_obj1.credentials:
                if cred.username == username:
                    cred_obj = cred
                    break
            if not cred_obj:
                cred_obj = Credentials()
                cred_obj.username = username
                actor_obj1.credentials.append(cred_obj)
                actor_obj1.alt_ids.append("UNAME:" + username)
            cred_obj.identity_provider = "SciON"
            cred_obj.authentication_service = "SciON IdM"
            cred_obj.password_salt = pwd_salt
            cred_obj.password_hash = pwd_hash
            self.rr.update(actor_obj1)
        else:
            self.idm_client.set_actor_credentials(actor_id, username, password)

        return actor_id

    def _get_user_by_email(self, email):
        user_objs_rq = ResourceQuery()
        user_objs_rq.set_filter(
            user_objs_rq.filter_type(RT.ActorIdentity),
            user_objs_rq.filter_attribute('details.contact.email', email))
        users = self.rr.find_resources_ext(query=user_objs_rq.get_query(), id_only=False)
        if users:
            return users[0]
        return None

    def update_user_contact(self, user_id='', contact=None, contact_entries=None):
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)
        self._validate_arg_obj("contact", contact, OT.ContactInformation, optional=True)
        if contact is None and not contact_entries:
            raise BadRequest("Missing contact arguments")
        address_fields = ("street_address", "city", "administrative_area", "postal_code", "country")
        old_contact = user_obj.details.contact
        old_address_parts = [getattr(old_contact, addr_attr) for addr_attr in address_fields if getattr(old_contact, addr_attr)]
        old_address_str = ", ".join(old_address_parts)

        if contact:
            user_obj.details.contact = contact
        elif contact_entries:
            for attr, att_val in contact_entries.iteritems():
                if att_val and hasattr(user_obj.details.contact, attr):
                    setattr(user_obj.details.contact, attr, att_val)
        user_obj.details.contact._validate()

        self.rr.update(user_obj)

    def delete_user(self, user_id=''):
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)

        self.idm_client.delete_actor_identity(user_id)

    def update_user_profile(self, user_id='', profile_entries=None):
        profile_entries = profile_entries or {}
        user_id = self._as_actor_id(user_id)
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)
        user_obj.details.profile.update(profile_entries)
        self.rr.update(user_obj)

    def get_user_profile(self, user_id='', settings_filter=None):
        settings_filter = settings_filter or []
        user_id = self._as_actor_id(user_id)
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)
        profile_data = user_obj.details.profile
        if settings_filter:
            profile_data = {k: v for k, v in profile_data.items() if k in settings_filter}
        return profile_data

    def change_password(self, old_pwd='', new_pwd=''):
        user_id = self._get_actor_id()
        user_obj = self._validate_resource_id("user_id", user_id, RT.ActorIdentity)
        self.idm_client.check_actor_credentials(user_obj.credentials[0].username, old_pwd)
        IdentityUtils.check_password_policy(new_pwd)
        self.idm_client.set_actor_credentials(user_id, user_obj.credentials[0].username , new_pwd)
