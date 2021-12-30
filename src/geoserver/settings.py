# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright 2019, GeoSolutions Sas.
# Jendrusk also was here
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

from geoserver.support import ResourceInfo, xml_property, write_bool, write_string, write_int


def write_settings(settings):
    def write(builder, settings):
        params = ["id", "contact", "charset", "numDecimals",
                  "onlineResource", "verbose", "verboseExceptions", "localWorkspaceIncludesPrefix" ]

        for param in params:
            if param == "contact":
                cparams = ["addressCity", "addressCountry", "addressType",
                           "contactEmail", "contactOrganization", "contactPerson", "contactPosition"]
                for cparam in cparams:
                    builder.start(cparam, dict())
                    builder.data(getattr(settings.contact, cparam))
                    builder.end(cparam)
            else:
                builder.start(param, dict())
                builder.data(getattr(settings, param))
                builder.end(param)

    return write


class Contact(object):
    def __init__(self, dom):
        self.addressCity = dom.find("addressCity").text if dom.find("addressCity") is not None else None
        self.addressCountry = dom.find("addressCountry").text if dom.find("addressCountry") is not None else None
        self.addressType = dom.find("addressType").text if dom.find("addressType") is not None else None
        self.contactEmail = dom.find("contactEmail").text if dom.find("contactEmail") is not None else None
        self.contactOrganization = dom.find("contactOrganization").text if dom.find("contactOrganization") is not None else None
        self.contactPerson = dom.find("contactPerson").text if dom.find("contactPerson") is not None else None
        self.contactPosition = dom.find("contactPosition").text if dom.find("contactPosition") is not None else None


class Settings(object):
    def __init__(self, dom):
        self.id = dom.find("id").text if dom.find("id") is not None else None
        self.contact = Contact(dom=dom)
        self.charset = dom.find("charset").text if dom.find("charset") is not None else None
        self.numDecimals = dom.find("numDecimals").text if dom.find("numDecimals") is not None else None
        self.onlineResource = dom.find("onlineResource").text if dom.find("onlineResource") is not None else None
        self.verbose = dom.find("verbose").text if dom.find("verbose") is not None else None
        self.verboseExceptions = dom.find("verboseExceptions").text if dom.find("verboseExceptions") is not None else None
        self.localWorkspaceIncludesPrefix = dom.find("localWorkspaceIncludesPrefix").text if dom.find("localWorkspaceIncludesPrefix") is not None else None
        self.contact = None


def write_dataclass(dataclass):
    def write(builder, dataclass):
        params = vars(dataclass)
        write_exclude = ["main_elem"]
        write_params = [x for x in params if x not in write_exclude]
        for param in write_params:
            builder.start(param, dict())
            builder.data(getattr(dataclass, param))
            builder.end(param)

    return write


class Jai(object):
    def __init__(self, dom):
        self.main_elem = "jai"
        self.allowInterpolation = dom.find("allowInterpolation").text if dom.find("allowInterpolation") is not None else None
        self.recycling = dom.find("recycling").text if dom.find("recycling") is not None else None
        self.tilePriority = dom.find("tilePriority").text if dom.find("tilePriority") is not None else None
        self.tileThreads = dom.find("tileThreads").text if dom.find("tileThreads") is not None else None
        self.memoryCapacity = dom.find("memoryCapacity").text if dom.find("memoryCapacity") is not None else None
        self.memoryThreshold = dom.find("memoryThreshold").text if dom.find("memoryThreshold") is not None else None
        self.imageIOCache = dom.find("imageIOCache").text if dom.find("imageIOCache") is not None else None
        self.pngAcceleration = dom.find("pngAcceleration").text if dom.find("pngAcceleration") is not None else None
        self.jpegAcceleration = dom.find("jpegAcceleration").text if dom.find("jpegAcceleration") is not None else None
        self.allowNativeMosaic = dom.find("allowNativeMosaic").text if dom.find("allowNativeMosaic") is not None else None
        self.allowNativeWarp = dom.find("allowNativeWarp").text if dom.find("allowNativeWarp") is not None else None


class CoverageAccess(object):
    def __init__(self, dom):
        self.main_elem = "coverageAccess"
        self.maxPoolSize = dom.find("maxPoolSize").text if dom.find("maxPoolSize") is not None else None
        self.corePoolSize = dom.find("corePoolSize").text if dom.find("corePoolSize") is not None else None
        self.keepAliveTime = dom.find("keepAliveTime").text if dom.find("keepAliveTime") is not None else None
        self.queueType = dom.find("queueType").text if dom.find("queueType") is not None else None
        self.imageIOCacheThreshold = dom.find("imageIOCacheThreshold").text if dom.find("imageIOCacheThreshold") is not None else None


class GlobalSettings(ResourceInfo):
    resource_type = "global"

    def __init__(self, catalog):
        super(GlobalSettings, self).__init__()
        self._catalog = catalog

    @property
    def catalog(self):
        return self._catalog

    @property
    def href(self):
        return urljoin(
            "{}/".format(self.catalog.service_url),
            "settings"
        )

    settings = xml_property("settings", Settings)
    jai = xml_property("jai", Jai)
    coverageAccess = xml_property("coverageAccess", CoverageAccess)
    updateSequence = xml_property("updateSequence", lambda x: int(x.text))
    featureTypeCacheSize = xml_property("featureTypeCacheSize", lambda x: int(x.text))
    globalServices = xml_property("globalServices", lambda x: x.text.lower() == 'true')
    xmlPostRequestLogBufferSize = xml_property("xmlPostRequestLogBufferSize", lambda x: int(x.text))

    writers = {
        'settings': write_settings("enabled"),
        'jai': write_dataclass("enabled"),
        'coverageAccess': write_dataclass("enabled"),
        'updateSequence': write_int("enabled"),
        'featureTypeCacheSize': write_int("enabled"),
        'globalServices': write_bool("enabled"),
        'xmlPostRequestLogBufferSize': write_int("enabled")
    }

    def __repr__(self):
        return "{} @ {}".format("settings", self.href)
