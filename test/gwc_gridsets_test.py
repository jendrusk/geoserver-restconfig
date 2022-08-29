import unittest
import string
import random
import os
from .utils import DBPARAMS
from .utils import GSPARAMS
import subprocess
import re
import time
from geoserver.catalog import Catalog
from geoserver.gwc_gridset import GridSet

if GSPARAMS['GEOSERVER_HOME']:
    dest = GSPARAMS['DATA_DIR']
    data = os.path.join(GSPARAMS['GEOSERVER_HOME'], 'data/release', '')
    if dest:
        os.system('rsync -v -a --delete %s %s' %
                  (data, os.path.join(dest, '')))
    else:
        os.system('git clean -dxf -- %s' % data)
    os.system("curl -XPOST --user '{user}':'{password}' '{url}/reload'".format(
        user=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'], url=GSPARAMS['GSURL']))

if GSPARAMS['GS_VERSION']:
    subprocess.Popen(["rm", "-rf", GSPARAMS['GS_BASE_DIR'] + "/gs"]).communicate()
    subprocess.Popen(["mkdir", GSPARAMS['GS_BASE_DIR'] + "/gs"]).communicate()
    subprocess.Popen(
        [
            "wget",
            "http://central.maven.org/maven2/org/eclipse/jetty/jetty-runner/9.4.5.v20170502/jetty-runner-9.4.5.v20170502.jar",
            "-P", GSPARAMS['GS_BASE_DIR'] + "/gs"
        ]
    ).communicate()

    subprocess.Popen(
        [
            "wget",
            "https://build.geoserver.org/geoserver/" + GSPARAMS['GS_VERSION'] + "/geoserver-" + GSPARAMS[
                'GS_VERSION'] + "-latest-war.zip",
            "-P", GSPARAMS['GS_BASE_DIR'] + "/gs"
        ]
    ).communicate()

    subprocess.Popen(
        [
            "unzip",
            "-o",
            "-d",
            GSPARAMS['GS_BASE_DIR'] + "/gs",
            GSPARAMS['GS_BASE_DIR'] + "/gs/geoserver-" + GSPARAMS['GS_VERSION'] + "-latest-war.zip"
        ]
    ).communicate()

    FNULL = open(os.devnull, 'w')

    match = re.compile(r'[^\d.]+')
    geoserver_short_version = match.sub('', GSPARAMS['GS_VERSION']).strip('.')
    if geoserver_short_version >= "2.15" or GSPARAMS['GS_VERSION'].lower() == 'master':
        java_executable = "/usr/local/lib/jvm/openjdk11/bin/java"
    else:
        java_executable = "/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java"

    print("geoserver_short_version: {}".format(geoserver_short_version))
    print("java_executable: {}".format(java_executable))
    proc = subprocess.Popen(
        [
            java_executable,
            "-Xmx1024m",
            "-Dorg.eclipse.jetty.server.webapp.parentLoaderPriority=true",
            "-jar", GSPARAMS['GS_BASE_DIR'] + "/gs/jetty-runner-9.4.5.v20170502.jar",
            "--path", "/geoserver", GSPARAMS['GS_BASE_DIR'] + "/gs/geoserver.war"
        ],
        stdout=FNULL, stderr=subprocess.STDOUT
    )
    child_pid = proc.pid
    print("Sleep (90)...")
    time.sleep(40)

ENUMS = {}


class GWCGridsetCreateTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.cat2 = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()

    def tearDown(self) -> None:
        self.cat.delete(self.gs)

    def test_create_gridset(self):
        self.gs = self.cat.create_gwc_gridset('test_gridset')
        self.gs.srs = 3857
        self.gs.extent = {'minx': -20037508.34, 'miny': -20037508.34, 'maxx': 20037508.34, 'maxy': 20037508.34}
        self.gs.resolutions = [156543.03390625, 78271.516953125, 39135.7584765625, 19567.87923828125, 9783.939619140625, 4891.9698095703125, 2445.9849047851562, 1222.9924523925781, 611.4962261962891, 305.74811309814453, 152.87405654907226, 76.43702827453613, 38.218514137268066, 19.109257068634033, 9.554628534317017]
        self.gs.scaleNames = ['EPSG:3857:0', 'EPSG:3857:1', 'EPSG:3857:2', 'EPSG:3857:3', 'EPSG:3857:4', 'EPSG:3857:5', 'EPSG:3857:6', 'EPSG:3857:7', 'EPSG:3857:8', 'EPSG:3857:9', 'EPSG:3857:10', 'EPSG:3857:11', 'EPSG:3857:12', 'EPSG:3857:13', 'EPSG:3857:14']
        self.gs.alignTopLeft = False
        self.gs.metersPerUnit = 1
        self.gs.pixelSize = 2.8E-4
        self.gs.tileHeight = 256
        self.gs.tileWidth = 256
        self.gs.yCoordinateFirst = False
        self.cat.save(self.gs)


class GWCGridsetsTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.cat2 = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.exclude_attrs = []
        self.exclude_attrs += [x for x in ENUMS.keys()]

    def tearDown(self) -> None:
        pass

    def test_get_gridsets(self):
        gs = self.cat.get_gwc_gridsets()
        self.assertGreater(len(gs), 0)
        for g in gs:
            self.assertIsInstance(g, GridSet)

    def test_get_gridset(self):
        gs = self.cat.get_gwc_gridsets()
        self.assertGreater(len(gs), 0)
        g = gs[0]
        gname = g.name
        tgs = self.cat.get_gwc_gridset(gname)
        self.assertEqual(tgs.name, gname)


class GWCGridsetsEditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.cat2 = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.exclude_attrs = ['name']
        self.exclude_attrs += [x for x in ENUMS.keys()]

        self.gs = self.cat.create_gwc_gridset('test_gridset')
        self.gs.srs = 3857
        self.gs.extent = {'minx': -20037508.34, 'miny': -20037508.34, 'maxx': 20037508.34, 'maxy': 20037508.34}
        self.gs.resolutions = [156543.03390625, 78271.516953125, 39135.7584765625, 19567.87923828125, 9783.939619140625,
                               4891.9698095703125, 2445.9849047851562, 1222.9924523925781, 611.4962261962891,
                               305.74811309814453, 152.87405654907226, 76.43702827453613, 38.218514137268066,
                               19.109257068634033, 9.554628534317017]
        self.gs.scaleNames = ['EPSG:3857:0', 'EPSG:3857:1', 'EPSG:3857:2', 'EPSG:3857:3', 'EPSG:3857:4', 'EPSG:3857:5',
                              'EPSG:3857:6', 'EPSG:3857:7', 'EPSG:3857:8', 'EPSG:3857:9', 'EPSG:3857:10',
                              'EPSG:3857:11', 'EPSG:3857:12', 'EPSG:3857:13', 'EPSG:3857:14']
        self.gs.alignTopLeft = False
        self.gs.metersPerUnit = 1
        self.gs.pixelSize = 2.8E-4
        self.gs.tileHeight = 256
        self.gs.tileWidth = 256
        self.gs.yCoordinateFirst = False
        self.cat.save(self.gs)

    def tearDown(self) -> None:
        self.cat.delete(self.gs)

    def test_simple_attrs(self):

        tgs = self.cat.get_gwc_gridset(self.gs.name)

        # test boolean
        attrs = [k for k, v in tgs.writers.items() if isinstance(getattr(tgs, k), bool) and k not in self.exclude_attrs]
        for attr in attrs:
            setattr(tgs, attr, False)
            self.cat.save(tgs)
            tgs.refresh()
            self.assertIsNone(tgs.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(tgs, attr))
            setattr(tgs, attr, True)
            self.cat.save(tgs)
            tgs.refresh()
            self.assertIsNone(tgs.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(tgs, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in tgs.writers.items() if
                 isinstance(getattr(tgs, k), str) and k not in self.exclude_attrs]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(tgs, attr, test_str)
            self.cat.save(tgs)
            tgs.refresh()
            self.assertIsNone(tgs.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(tgs, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in tgs.writers.keys() if type(getattr(tgs, k)) == int and k not in self.exclude_attrs]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(tgs, attr, test_int)
            self.cat.save(tgs)
            tgs.refresh()
            self.assertIsNone(tgs.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(tgs, attr), test_int, msg="Invalid value for object {}".format(attr))
