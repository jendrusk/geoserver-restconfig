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
from geoserver.security import User

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

class GWCLayerTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.cat2 = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.exclude_attrs = ['id', 'name']

    def tearDown(self) -> None:
        pass

    def test_get_layers(self):
        gwc_layers = self.cat.get_gwc_layers()
        self.assertGreater(len(gwc_layers),0)

    def test_simple_attrs(self):

        gwc_layers = self.cat.get_gwc_layers()
        gwc_layer = gwc_layers[0]

        # test boolean
        attrs = [k for k, v in gwc_layer.writers.items() if isinstance(getattr(gwc_layer, k), bool) and k not in self.exclude_attrs]
        # attrs = [k for k, v in gwc_layer.writers.items() if isinstance(getattr(gwc_layer, k), bool)]
        for attr in attrs:
            setattr(gwc_layer, attr, False)
            self.cat.save(gwc_layer)
            gwc_layer.refresh()
            self.assertIsNone(gwc_layer.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(gwc_layer, attr))
            setattr(gwc_layer, attr, True)
            self.cat.save(gwc_layer)
            gwc_layer.refresh()
            self.assertIsNone(gwc_layer.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(gwc_layer, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in gwc_layer.writers.items() if
                 isinstance(getattr(gwc_layer, k), str) and k not in self.exclude_attrs]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(gwc_layer, attr, test_str)
            self.cat.save(gwc_layer)
            gwc_layer.refresh()
            self.assertIsNone(gwc_layer.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(gwc_layer, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in gwc_layer.writers.keys() if type(getattr(gwc_layer, k)) == int and k not in self.exclude_attrs]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(gwc_layer, attr, test_int)
            self.cat.save(gwc_layer)
            gwc_layer.refresh()
            self.assertIsNone(gwc_layer.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(gwc_layer, attr), test_int, msg="Invalid value for object {}".format(attr))

    def test_mime_formats(self):

        vector_formats = [
            # 'application/vnd.mapbox-vector-tile',
            # 'application/json;type=geojson',
            'application/json;type=topojson'
        ]

        gwc_layers = self.cat.get_gwc_layers()
        gwc_layer = gwc_layers[0]

        old_formats = gwc_layer.mimeFormats
        new_formats = gwc_layer.mimeFormats
        for vf in vector_formats:
            new_formats.append(vf)
        gwc_layer.mimeFormats = new_formats
        self.cat.save(gwc_layer)
        gwc_layer.refresh()

        self.assertIsNone(gwc_layer.dirty.get('mimeFormats'), msg="Attribute {} still in dirty list".format('mimeFormats'))
        for vf in vector_formats:
            self.assertIn(vf, gwc_layer.mimeFormats, msg="Invalid value for object {}".format(vf))

        gwc_layer.mimeFormats = old_formats
        self.cat.save(gwc_layer)
        gwc_layer.refresh()

        for vf in vector_formats:
            self.assertNotIn(vf, gwc_layer.mimeFormats, msg="Invalid value for object {}".format(vf))
