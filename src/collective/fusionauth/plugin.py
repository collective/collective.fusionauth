# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees import OOBTree
from collective.fusionauth.interfaces import IFusionAuthPlugin
from Products.PlonePAS import interfaces as plonepas_interfaces
from Products.PlonePAS.plugins.group import PloneGroup
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PluggableAuthService.permissions import ManageGroups
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer

import json
import logging
import os
import time
import requests


logger = logging.getLogger("collective.fusionauth")
zmidir = os.path.join(os.path.dirname(__file__), "zmi")


process_time = time.process_time


def manage_addFusionAuthPlugin(dispatcher, id, title="", RESPONSE=None, **kw):
    """Create an instance of a LDAP Plugin.
    """
    FusionAuthPlugin = FusionAuthPlugin(id, title, **kw)
    dispatcher._setObject(FusionAuthPlugin.getId(), FusionAuthPlugin)
    if RESPONSE is not None:
        RESPONSE.redirect("manage_workspace")


manage_addFusionAuthPluginForm = PageTemplateFile(
    os.path.join(zmidir, "add_plugin.pt"), globals(), __name__="addFusionAuthPlugin"
)



@implementer(
    IFusionAuthPlugin,
    pas_interfaces.IAuthenticationPlugin,
)
class FusionAuthPlugin(BasePlugin):
    """Glue layer for making node.ext.ldap available to PAS.
    """

    security = ClassSecurityInfo()
    meta_type = "LDAP Plugin"
    manage_options = (
        {"label": "LDAP Settings", "action": "manage_FusionAuthPlugin"},
    ) + BasePlugin.manage_options

    # Tell PAS not to swallow our exceptions
    _dont_swallow_my_exceptions = False

    def __init__(self, id, title=None, **kw):
        self._setId(id)
        self.title = title
        self.init_settings()
        self.plugin_caching = True

    def init_settings(self):
        self.settings = OOBTree.OOBTree()

    @security.private
    def is_plugin_active(self, iface):
        pas = self._getPAS()
        ids = pas.plugins.listPluginIds(iface)
        return self.getId() in ids

    @security.public
    def authenticateCredentials(self, credentials):
        """credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        
        default = None
        if not self.is_plugin_active(pas_interfaces.IAuthenticationPlugin):
            return default
        login = credentials.get("login")
        pw = credentials.get("password")
        if not (login and pw):
            return None 

        url = "http://localhost:9011/api/login"
        application_main = "b31533fc-2254-40ea-9572-e6040e942a6b"
        application_app = "3c219e58-ed0e-4b18-ad48-f4f92793ae32"

        payload = { "loginId": login, "password": pw, "applicationId": application_app}
            
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': application_main}

        response = requests.post(url, headers=headers, data = json.dumps(payload))
        if response.status_code == 202:
            return response.json()


InitializeClass(FusionAuthPlugin)
