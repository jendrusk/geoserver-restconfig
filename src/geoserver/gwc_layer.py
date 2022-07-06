try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin

from geoserver.support import (
    ResourceInfo, StaticResourceInfo, xml_property,
    write_bool, read_bool,read_string, string_list, read_int, write_string, write_int, write_string_list,read_int_list, write_int_list,
    read_extent, write_extent)


def gwclayer_from_index(catalog, node):
    gwclayer_name = node.find("name").text
    return GeoServerLayer(catalog, gwclayer_name)


def read_grid_subsets(node):
    return [GridSubset(subset) for subset in node.findall("gridSubset")]


def write_grid_subsets(name):
    def write(builder, lst):
        builder.start(name, dict())
        for sbc in lst:
            sbc.serialize_all(builder)
        builder.end(name)
    return write


class GridSubset(StaticResourceInfo):
    resource_type = "gridSubset"

    def __init__(self, dom):
        super(GridSubset, self).__init__()
        self.dom = dom

    def serialize(self, builder):
        # GeoServer will disable the resource if we omit the <enabled> tag,
        # so force it into the dirty dict before writing
        if hasattr(self, "enabled"):
            self.dirty['enabled'] = self.enabled

        if hasattr(self, "advertised"):
            self.dirty['advertised'] = self.advertised

        for k, writer in self.writers.items():

            if hasattr(self, k) and issubclass(type(getattr(self, k)), StaticResourceInfo):
                attr = getattr(self, k)
                if attr.dirty:
                    attr.serialize_all(builder)
            elif k in self.dirty:
                val = self.dirty[k]
                writer(builder, val)
            elif self.write_all and hasattr(self, k):
                attr = getattr(self, k)
                val = self.dirty[k] if self.dirty.get(k) else attr
                if val is not None:
                    writer(builder, val)
            elif self.write_all:
                attr = None

    gridSetName = xml_property("gridSetName", read_string)
    extent = xml_property("extent", read_extent)
    zoomStart = xml_property("zoomStart", read_int)
    zoomStop = xml_property("zoomStop", read_int)

    writers = {
    "gridSetName": write_string("gridSetName"),
    "extent": write_extent("extent"),
    "zoomStart": write_int("zoomStart"),
    "zoomStop": write_int("zoomStop"),
    }


class GeoServerLayer(ResourceInfo):
    resource_type = "GeoServerLayer"
    save_method = "PUT"

    def __init__(self, catalog, layer_name):
        super(GeoServerLayer, self).__init__()
        self._catalog = catalog
        self._layer_name = layer_name
        self.write_all = True

    @property
    def catalog(self):
        return self._catalog

    @property
    def layer_name(self):
        return self._layer_name

    @property
    def href(self):
        return "{gwc_url}/layers/{layer_name}".format(gwc_url=self.catalog.gwc_url, layer_name=self.layer_name)

    id = xml_property("id", read_string)
    enabled = xml_property("enabled", read_bool)
    inMemoryCached = xml_property("inMemoryCached", read_bool)
    name = xml_property("name", read_string)
    mimeFormats = xml_property("mimeFormats", string_list)
    gridSubsets = xml_property("gridSubsets", read_grid_subsets)
    metaWidthHeight = xml_property("metaWidthHeight", read_int_list)
    expireCache = xml_property("expireCache", read_int)
    expireClients = xml_property("expireClients", read_int)
    parameterFilters = None
    gutter = xml_property("gutter", read_int)

    writers = {
        'id': write_string("id"),
        'enabled': write_bool("enabled"),
        'inMemoryCached': write_bool("inMemoryCached"),
        'name': write_string("name"),
        'mimeFormats': write_string_list("mimeFormats"),
        'gridSubsets': write_grid_subsets("gridSubsets"),
        'metaWidthHeight': write_int_list("metaWidthHeight"),
        'expireCache': write_int("expireCache"),
        'expireClients': write_int("expireClients"),
        # 'parameterFilters': None,
        'gutter': write_int("gutter"),
    }

    def __repr__(self):
        return "{} @ {}".format(self.layer_name, self.href)