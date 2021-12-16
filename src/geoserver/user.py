# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright 2019, GeoSolutions Sas.
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
#
#########################################################################
try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin

from geoserver.support import ResourceInfo, xml_property, write_bool


def user_from_index(catalog, node):
    user_name = node.find("userName").text
    password = node.find("password").text if node.find("password") else None
    return User(catalog, user_name, password)


class User(ResourceInfo):
    resource_type = "user"

    def __init__(self, catalog, user_name, password):
        super(User, self).__init__()
        self._catalog = catalog
        self._user_name = user_name
        self._password = password
        # self._enabled = enabled

    @property
    def catalog(self):
        return self._catalog

    @property
    def user_name(self):
        return self._user_name

    @property
    def password(self):
        return self._password

    # @property
    # def enabled(self):
    #     return self._enabled

    @property
    def href(self):
        return urljoin(
            "{}/".format(self.catalog.service_url),
            "security/usergroup/users/{}".format(self.user_name)
        )

    # @property
    # def coveragestore_url(self):
    #     return urljoin(
    #         "{}/".format(self.catalog.service_url),
    #         "users/{}/coveragestores.xml".format(self.name)
    #     )
    #
    # @property
    # def datastore_url(self):
    #     return urljoin(
    #         "{}/".format(self.catalog.service_url),
    #         "users/{}/datastores.xml".format(self.name)
    #     )
    #
    # @property
    # def wmsstore_url(self):
    #     return urljoin(
    #         "{}/".format(self.catalog.service_url),
    #         "users/{}/wmsstores.xml".format(self.name)
    #     )

    enabled = xml_property("enabled", lambda x: x.lower() == 'true')
    writers = {
        'enabled': write_bool("enabled")
    }

    def __repr__(self):
        return "{} @ {}".format(self.name, self.href)
