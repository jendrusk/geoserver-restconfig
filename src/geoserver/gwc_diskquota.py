try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin

from geoserver.support import (
    ResourceInfo, StaticResourceInfo, xml_property,
    write_bool, read_bool,read_string, string_list, read_int, write_string, write_int, write_string_list,read_int_list, write_int_list,
    read_extent, write_extent, )


def read_quota(node):
    id = node.find('id')
    bt = node.find('bytes')
    if id is not None and bt is not None:
        return GwcQuota(id.text, bt.text)


def write_quota(name):
    def write(builder, cls):
        builder.start(name, dict())
        builder.start('value', dict())
        builder.data(cls.bt)
        builder.end('value')
        builder.start('units', dict())
        builder.data('B')
        builder.end('units')
        builder.end(name)
    return write


def gwcquotaconfiguration_from_index(catalog, href):
    return GwcQuotaConfiguration(catalog, href)


class GwcQuota:
    def __init__(self, id, bt):
        self.id = id
        self.bt = bt


def read_layer_quotas(node):
    # ommited - no settings in GUI, documentation broken
    pass


def write_layer_quotas(name):
    # ommited - no settings in GUI, documentation broken
    def write(builder, lst):
        builder.start(name, dict())
        builder.end(name)
    return write


class LayerQuota(StaticResourceInfo):
    def __init__(self, dom):
        super(LayerQuota, self).__init__()
        self.dom = dom

    layer = xml_property('layer', read_string)
    expirationPolicyName = xml_property('expirationPolicyName', read_string)
    quota = xml_property('quota', read_quota)

    writers = {
    "layer": write_string("layer"),
    "expirationPolicyName": write_string("expirationPolicyName"),
    "quota": write_quota("quota")
    }


class GwcQuotaConfiguration(ResourceInfo):

    resource_type = "gwcQuotaConfiguration"
    save_method = "PUT"

    def __init__(self, catalog, href):
        super(GwcQuotaConfiguration, self).__init__()
        self._catalog = catalog
        self.href = href
        self.write_all = True

    @property
    def catalog(self):
        return self._catalog

    enabled = xml_property('enabled', read_bool)
    diskBlockSize = xml_property('diskBlockSize', read_int)
    cacheCleanUpFrequency = xml_property('cacheCleanUpFrequency', read_int)
    cacheCleanUpUnits = xml_property('cacheCleanUpUnits', read_string)
    maxConcurrentCleanUps = xml_property('maxConcurrentCleanUps', read_int)
    globalExpirationPolicyName = xml_property('globalExpirationPolicyName', read_string)
    globalQuota = xml_property('globalQuota', read_quota)
    layerQuotas = xml_property('layerQuotas', read_layer_quotas)

    writers = {
        "enabled": write_bool("enabled"),
        "diskBlockSize": write_int("diskBlockSize"),
        "cacheCleanUpFrequency": write_int("cacheCleanUpFrequency"),
        "cacheCleanUpUnits": write_string("cacheCleanUpUnits"),
        "maxConcurrentCleanUps": write_int("maxConcurrentCleanUps"),
        "globalExpirationPolicyName": write_string("globalExpirationPolicyName"),
        "globalQuota": write_quota("globalQuota"),
        "layerQuotas": write_layer_quotas("layerQuotas")
    }

#     def __init__(self, catalog, layer_name):
#         super(GeoServerLayer, self).__init__()
#         self._catalog = catalog
#         self._layer_name = layer_name
#         self.write_all = True




#

#
#
# def read_grid_subsets(node):
#     return [GridSubset(subset) for subset in node.findall("gridSubset")]
#
#
# def write_grid_subsets(name):
#     def write(builder, lst):
#         builder.start(name, dict())
#         for sbc in lst:
#             sbc.serialize_all(builder)
#         builder.end(name)
#     return write
#
#
# class GridSubset(StaticResourceInfo):
#     resource_type = "gridSubset"
#
#     def __init__(self, dom):
#         super(GridSubset, self).__init__()
#         self.dom = dom
#
#     def serialize(self, builder):
#         # GeoServer will disable the resource if we omit the <enabled> tag,
#         # so force it into the dirty dict before writing
#         if hasattr(self, "enabled"):
#             self.dirty['enabled'] = self.enabled
#
#         if hasattr(self, "advertised"):
#             self.dirty['advertised'] = self.advertised
#
#         for k, writer in self.writers.items():
#
#             if hasattr(self, k) and issubclass(type(getattr(self, k)), StaticResourceInfo):
#                 attr = getattr(self, k)
#                 if attr.dirty:
#                     attr.serialize_all(builder)
#             elif k in self.dirty:
#                 val = self.dirty[k]
#                 writer(builder, val)
#             elif self.write_all and hasattr(self, k):
#                 attr = getattr(self, k)
#                 val = self.dirty[k] if self.dirty.get(k) else attr
#                 if val is not None:
#                     writer(builder, val)
#             elif self.write_all:
#                 attr = None
#
#     gridSetName = xml_property("gridSetName", read_string)
#     extent = xml_property("extent", read_extent)
#     zoomStart = xml_property("zoomStart", read_int)
#     zoomStop = xml_property("zoomStop", read_int)
#
#     writers = {
#     "gridSetName": write_string("gridSetName"),
#     "extent": write_extent("extent"),
#     "zoomStart": write_int("zoomStart"),
#     "zoomStop": write_int("zoomStop"),
#     }
#
#
# class GeoServerLayer(ResourceInfo):
#     resource_type = "GeoServerLayer"
#     save_method = "PUT"
#
#     def __init__(self, catalog, layer_name):
#         super(GeoServerLayer, self).__init__()
#         self._catalog = catalog
#         self._layer_name = layer_name
#         self.write_all = True
#
#     @property
#     def catalog(self):
#         return self._catalog
#
#     @property
#     def layer_name(self):
#         return self._layer_name
#
#     @property
#     def href(self):
#         return "{gwc_url}/layers/{layer_name}".format(gwc_url=self.catalog.gwc_url, layer_name=self.layer_name)
#
#     id = xml_property("id", read_string)
#     enabled = xml_property("enabled", read_bool)
#     inMemoryCached = xml_property("inMemoryCached", read_bool)
#     name = xml_property("name", read_string)
#     mimeFormats = xml_property("mimeFormats", string_list)
#     gridSubsets = xml_property("gridSubsets", read_grid_subsets)
#     metaWidthHeight = xml_property("metaWidthHeight", read_int_list)
#     expireCache = xml_property("expireCache", read_int)
#     expireClients = xml_property("expireClients", read_int)
#     parameterFilters = None
#     gutter = xml_property("gutter", read_int)
#
#     writers = {
#         'id': write_string("id"),
#         'enabled': write_bool("enabled"),
#         'inMemoryCached': write_bool("inMemoryCached"),
#         'name': write_string("name"),
#         'mimeFormats': write_string_list("mimeFormats"),
#         'gridSubsets': write_grid_subsets("gridSubsets"),
#         'metaWidthHeight': write_int_list("metaWidthHeight"),
#         'expireCache': write_int("expireCache"),
#         'expireClients': write_int("expireClients"),
#         # 'parameterFilters': None,
#         'gutter': write_int("gutter"),
#     }
#
#     def __repr__(self):
#         return "{} @ {}".format(self.layer_name, self.href)