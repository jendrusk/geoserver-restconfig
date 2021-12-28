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


class ServicesTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.bkp_cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()

        # backups
        self.bkp_wms_srv = self.bkp_cat.get_services(ogc_type="wms")[0]
        self.bkp_wms_srv.dirty = {k: getattr(self.bkp_wms_srv, k) for k, v in self.bkp_wms_srv.writers.items()}
        self.bkp_wfs_srv = self.bkp_cat.get_services(ogc_type="wfs")[0]
        self.bkp_wfs_srv.dirty = {k: getattr(self.bkp_wfs_srv, k) for k, v in self.bkp_wfs_srv.writers.items()}
        self.bkp_wcs_srv = self.bkp_cat.get_services(ogc_type="wcs")[0]
        self.bkp_wcs_srv.dirty = {k: getattr(self.bkp_wcs_srv, k) for k, v in self.bkp_wcs_srv.writers.items()}
        # self.bkp_wmts_srv = self.bkp_cat.get_services(ogc_type="wmts")[0]
        # self.bkp_wmts_srv.dirty = {k: getattr(self.bkp_wmts_srv, k) for k, v in self.bkp_wmts_srv.writers.items()}

        # test workspace
        self.test_ws = self.cat.get_workspace("services_test_ws")
        if self.test_ws is None:
            self.test_ws = self.cat.create_workspace("services_test_ws", uri=self.cat.service_url)

        # enums for tests
        self.wfs_enums = {
            "interpolation": ["Nearest", "Bilinear", "Bicubic"]
        }
        self.wfs_enums = {
            "serviceLevel": ["BASIC", "TRANSACTIONAL", "COMPLETE"]
        }
        self.wcs_enums = {}
        self.wmts_enums = {}

    def tearDown(self) -> None:
        self.cat.delete(self.test_ws, recurse=True)

        # restore backups
        self.bkp_cat.save(self.bkp_wms_srv)
        self.bkp_cat.save(self.bkp_wfs_srv)
        self.bkp_cat.save(self.bkp_wcs_srv)
        #self.bkp_cat.save(self.bkp_wmts_srv)

    def test_global_wms(self):

        self.wms_srv = self.cat.get_services(ogc_type="wms")[0]
        wms_srv = self.cat.get_services(ogc_type="wms")[0]

        # test boolean
        attrs = [k for k, v in wms_srv.writers.items() if isinstance(getattr(wms_srv, k), bool)]
        for attr in attrs:
            setattr(wms_srv, attr, False)
            self.cat.save(wms_srv)
            wms_srv.refresh()
            self.assertIsNone(wms_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(wms_srv, attr))
            setattr(wms_srv, attr, True)
            self.cat.save(wms_srv)
            wms_srv.refresh()
            self.assertIsNone(wms_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(wms_srv, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in wms_srv.writers.items() if
                 isinstance(getattr(wms_srv, k), str) and k not in self.wfs_enums.keys()]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(wms_srv, attr, test_str)
            self.cat.save(wms_srv)
            wms_srv.refresh()
            self.assertIsNone(wms_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wms_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test enums
        attrs = [k for k in self.wfs_enums.keys()]
        for attr in attrs:
            test_str = self.wfs_enums[attr][random.randint(0, len(self.wfs_enums[attr]))]
            setattr(wms_srv, attr, test_str)
            self.cat.save(wms_srv)
            wms_srv.refresh()
            self.assertIsNone(wms_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wms_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in wms_srv.writers.keys() if type(getattr(wms_srv, k)) == int]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(wms_srv, attr, test_int)
            self.cat.save(wms_srv)
            wms_srv.refresh()
            self.assertIsNone(wms_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wms_srv, attr), test_int, msg="Invalid value for object {}".format(attr))

    def test_global_wfs(self):

        self.wfs_srv = self.cat.get_services(ogc_type="wfs")[0]
        wfs_srv = self.cat.get_services(ogc_type="wfs")[0]

        # test boolean
        attrs = [k for k, v in wfs_srv.writers.items() if isinstance(getattr(wfs_srv, k), bool)]
        for attr in attrs:
            setattr(wfs_srv, attr, False)
            self.cat.save(wfs_srv)
            wfs_srv.refresh()
            self.assertIsNone(wfs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(wfs_srv, attr))
            setattr(wfs_srv, attr, True)
            self.cat.save(wfs_srv)
            wfs_srv.refresh()
            self.assertIsNone(wfs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(wfs_srv, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in wfs_srv.writers.items() if
                 isinstance(getattr(wfs_srv, k), str) and k not in self.wfs_enums.keys()]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(wfs_srv, attr, test_str)
            self.cat.save(wfs_srv)
            wfs_srv.refresh()
            self.assertIsNone(wfs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wfs_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test enums
        attrs = [k for k in self.wfs_enums.keys()]
        for attr in attrs:
            test_str = self.wfs_enums[attr][random.randint(0, len(self.wfs_enums[attr]))]
            setattr(wfs_srv, attr, test_str)
            self.cat.save(wfs_srv)
            wfs_srv.refresh()
            self.assertIsNone(wfs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wfs_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in wfs_srv.writers.keys() if type(getattr(wfs_srv, k)) == int]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(wfs_srv, attr, test_int)
            self.cat.save(wfs_srv)
            wfs_srv.refresh()
            self.assertIsNone(wfs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wfs_srv, attr), test_int, msg="Invalid value for object {}".format(attr))

    def test_global_wcs(self):

        self.wcs_srv = self.cat.get_services(ogc_type="wcs")[0]
        wcs_srv = self.cat.get_services(ogc_type="wcs")[0]

        # test boolean
        attrs = [k for k, v in wcs_srv.writers.items() if isinstance(getattr(wcs_srv, k), bool)]
        for attr in attrs:
            setattr(wcs_srv, attr, False)
            self.cat.save(wcs_srv)
            wcs_srv.refresh()
            self.assertIsNone(wcs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(wcs_srv, attr))
            setattr(wcs_srv, attr, True)
            self.cat.save(wcs_srv)
            wcs_srv.refresh()
            self.assertIsNone(wcs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(wcs_srv, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in wcs_srv.writers.items() if
                 isinstance(getattr(wcs_srv, k), str) and k not in self.wcs_enums.keys()]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(wcs_srv, attr, test_str)
            self.cat.save(wcs_srv)
            wcs_srv.refresh()
            self.assertIsNone(wcs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wcs_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test enums
        attrs = [k for k in self.wfs_enums.keys()]
        for attr in attrs:
            test_str = self.wfs_enums[attr][random.randint(0, len(self.wfs_enums[attr]))]
            setattr(wcs_srv, attr, test_str)
            self.cat.save(wcs_srv)
            wcs_srv.refresh()
            self.assertIsNone(wcs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wcs_srv, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in wcs_srv.writers.keys() if type(getattr(wcs_srv, k)) == int]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(wcs_srv, attr, test_int)
            self.cat.save(wcs_srv)
            wcs_srv.refresh()
            self.assertIsNone(wcs_srv.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(wcs_srv, attr), test_int, msg="Invalid value for object {}".format(attr))

    # def test_workspace_wms(self):
    #
    #     wms_srvs = self.cat.get_services(ogc_type="wms")
    #     wms_srvs_ws = [x for x in wms_srvs if x.workspace == self.test_ws]
    #     self.assertEqual(len(wms_srvs_ws), 0)
    #
    #     wms_srv = self.cat.create_service(ogc_type="wms", workspace=self.test_ws.name)


if __name__ == '__main__':
    ans = input("This test could break your Geoserver configuration - are U sure? (y/n)")
    if ans.lower() == "y":
        unittest.main()
    else:
        exit(0)

# TODO: Add test for metadata
# TODO: Add test for metadataLink
# TODO: Add test for versions
# TODO: Add test for keywords
