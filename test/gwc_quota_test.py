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
from geoserver.gwc_diskquota import GwcQuotaConfiguration

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

ENUMS = {
    'cacheCleanUpUnits': ['SECONDS', 'MINUTES', 'HOURS', 'DAYS'],
    'globalExpirationPolicyName': ['LRU', 'LSU']
}


class GWCQuotaSeetingsTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.cat2 = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.exclude_attrs = []
        self.exclude_attrs += [x for x in ENUMS.keys()]

    def tearDown(self) -> None:
        pass

    def test_get_quota(self):
        lq = self.cat.get_gwc_quota()
        self.assertIsInstance(lq, GwcQuotaConfiguration)

    def test_simple_attrs(self):

        gwc_quota = self.cat.get_gwc_quota()

        # test boolean
        attrs = [k for k, v in gwc_quota.writers.items() if isinstance(getattr(gwc_quota, k), bool) and k not in self.exclude_attrs]
        for attr in attrs:
            setattr(gwc_quota, attr, False)
            self.cat.save(gwc_quota)
            gwc_quota.refresh()
            self.assertIsNone(gwc_quota.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertFalse(getattr(gwc_quota, attr))
            setattr(gwc_quota, attr, True)
            self.cat.save(gwc_quota)
            gwc_quota.refresh()
            self.assertIsNone(gwc_quota.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertTrue(getattr(gwc_quota, attr), msg="Invalid value for object {}".format(attr))

        # test string
        attrs = [k for k, v in gwc_quota.writers.items() if
                 isinstance(getattr(gwc_quota, k), str) and k not in self.exclude_attrs]
        for attr in attrs:
            test_str = ''.join(random.sample(string.ascii_lowercase, 10))
            setattr(gwc_quota, attr, test_str)
            self.cat.save(gwc_quota)
            gwc_quota.refresh()
            self.assertIsNone(gwc_quota.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(gwc_quota, attr), test_str, msg="Invalid value for object {}".format(attr))

        # test int
        attrs = [k for k in gwc_quota.writers.keys() if type(getattr(gwc_quota, k)) == int and k not in self.exclude_attrs]
        for attr in attrs:
            test_int = random.randint(1, 20)
            setattr(gwc_quota, attr, test_int)
            self.cat.save(gwc_quota)
            gwc_quota.refresh()
            self.assertIsNone(gwc_quota.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(gwc_quota, attr), test_int, msg="Invalid value for object {}".format(attr))

    def test_enums(self):
        gwc_quota = self.cat.get_gwc_quota()
        for attr, vals in ENUMS.items():
            test_int = random.randint(0, len(vals)-1)
            setattr(gwc_quota, attr, vals[test_int])
            self.cat.save(gwc_quota)
            gwc_quota.refresh()
            self.assertIsNone(gwc_quota.dirty.get(attr), msg="Attribute {} still in dirty list".format(attr))
            self.assertEqual(getattr(gwc_quota, attr), vals[test_int], msg="Invalid value for object {}".format(attr))


    def test_global_quota(self):
        gwc_quota = self.cat.get_gwc_quota()
        test_int = random.randint(0, 100)
        gwc_quota.bt = test_int
        self.cat.save(gwc_quota)
        gwc_quota.refresh()
        self.assertIsNone(gwc_quota.dirty.get('bt'), msg="Attribute {} still in dirty list".format('bt'))
        self.assertEqual(getattr(gwc_quota, 'bt'), test_int, msg="Invalid value for object {}".format('bt'))

