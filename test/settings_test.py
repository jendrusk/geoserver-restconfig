from copy import deepcopy
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
from geoserver.support import StaticResourceInfo

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


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.bkp_cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.bkp_global_settings = deepcopy(self.bkp_cat.get_global_settings())
        self.global_enums = {}
        self.settings_enums = {}
        self.contact_enums = {}
        self.coverageAccess_enums = {"queueType": ["UNBOUNDED", "DIRECT"]}
        self.jai_enums = {}

    def tearDown(self) -> None:
        self.bkp_global_settings.dirty_all()
        self.bkp_cat.save(self.bkp_global_settings)

    def test_get_settings(self):
        glob = self.cat.get_global_settings()
        self.assertIsNotNone(glob)

    def test_set_global(self):

        test_class = self.cat.get_global_settings()

        # test boolean
        attrs = [k for k, v in test_class.writers.items() if isinstance(getattr(test_class, k), bool)]
        enums = getattr(self, test_class.resource_type + "_enums")
        for attr in attrs:
            setattr(test_class, attr, False)
            self.cat.save(test_class)
            test_class.refresh()
            self.assertIsNone(test_class.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(test_class, attr))
            setattr(test_class, attr, True)
            self.cat.save(test_class)
            test_class.refresh()
            self.assertIsNone(test_class.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(test_class, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in test_class.writers.items() if
                 isinstance(getattr(test_class, k), str) and k not in enums.keys()]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(test_class, attr, test_str)
            self.cat.save(test_class)
            test_class.refresh()
            self.assertIsNone(test_class.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(test_class, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test enums
        attrs = [k for k in enums.keys()]
        for attr in attrs:
            test_str = enums[attr][random.randint(0, len(enums[attr])-1)]
            setattr(test_class, attr, test_str)
            self.cat.save(test_class)
            test_class.refresh()
            self.assertIsNone(test_class.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(test_class, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in test_class.writers.keys() if type(getattr(test_class, k)) == int]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(test_class, attr, test_int)
            self.cat.save(test_class)
            test_class.refresh()
            self.assertIsNone(test_class.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(test_class, attr), test_int, msg="Invalid value for object {}".format(attr))

    def test_set_settings(self):
        glob = self.cat.get_global_settings()
        subclasses = [x for x in glob.writers.keys() if issubclass(type(getattr(glob, x)), StaticResourceInfo)]

        for subcls in subclasses:

            # test boolean
            attrs = [k for k, v in getattr(glob, subcls).writers.items() if isinstance(getattr(getattr(glob, subcls), k), bool)]
            enums = getattr(self, getattr(glob, subcls).resource_type + "_enums")

            for attr in attrs:
                setattr(getattr(glob, subcls), attr, False)
                self.cat.save(glob)
                glob.refresh()
                self.assertIsNone(getattr(glob, subcls).dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
                self.assertFalse(getattr(getattr(glob, subcls), attr))
                setattr(getattr(glob, subcls), attr, True)
                self.cat.save(glob)
                glob.refresh()
                self.assertIsNone(getattr(glob, subcls).dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
                self.assertTrue(getattr(getattr(glob, subcls), attr), msg="Invalid value for object {}".format(attr))

            # test string
            attrs = [k for k, v in getattr(glob, subcls).writers.items() if
                     isinstance(getattr(getattr(glob, subcls), k), str) and k not in enums.keys()]
            for attr in attrs:
                test_str = ''.join(random.sample(string.ascii_lowercase, 10))
                setattr(getattr(glob, subcls), attr, test_str)
                self.cat.save(glob)
                glob.refresh()
                self.assertIsNone(getattr(glob, subcls).dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
                self.assertEqual(getattr(getattr(glob, subcls), attr), test_str,
                                 msg="Invalid value for object {}".format(attr))

            # test enums
            attrs = [k for k in enums.keys()]
            for attr in attrs:
                test_str = enums[attr][random.randint(0, len(enums[attr])-1)]
                setattr(getattr(glob, subcls), attr, test_str)
                self.cat.save(glob)
                glob.refresh()
                self.assertIsNone(getattr(glob, subcls).dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
                self.assertEqual(getattr(getattr(glob, subcls), attr), test_str,
                                 msg="Invalid value for object {}".format(attr))

            # test int
            attrs = [k for k in getattr(glob, subcls).writers.keys() if type(getattr(getattr(glob, subcls), k)) == int]
            for attr in attrs:
                test_int = random.randint(1, 20)
                setattr(getattr(glob, subcls), attr, test_int)
                self.cat.save(glob)
                glob.refresh()
                self.assertIsNone(getattr(glob, subcls).dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
                self.assertEqual(getattr(getattr(glob, subcls), attr), test_int,
                                 msg="Invalid value for object {}".format(attr))




