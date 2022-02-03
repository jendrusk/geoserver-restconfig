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


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.bkp_cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.gs_version = self.cat.get_short_version()
        self.bkp_masterpwd = self.bkp_cat.get_master_pwd()
        self.bkp_my_pwd = self.cat.password

    def tearDown(self) -> None:
        self.bkp_cat.set_master_pwd(self.bkp_masterpwd)
        self.bkp_cat.set_my_pwd(self.bkp_my_pwd)
        usrs = [x for x in self.cat.get_users(names="test_usr12")]
        if len(usrs) > 0:
            self.cat.delete(usrs[0])

    def test_get_users(self):
        users = self.cat.get_users()
        self.assertGreater(len(users),0)

    def test_get_master_pwd(self):
        master_pwd = self.cat.get_master_pwd()
        self.assertIsNotNone(master_pwd)
        self.assertEqual(master_pwd, "geoserver")

    def test_set_master_pwd(self):
        test_pwd = ''.join(random.sample(string.ascii_lowercase, 10))
        master_pwd = self.cat.set_master_pwd(new_pwd=test_pwd)
        self.assertIsNotNone(master_pwd)
        self.assertEqual(master_pwd, test_pwd)
        new_master_pwd = self.cat.get_master_pwd()
        self.assertEqual(new_master_pwd, test_pwd)

    def test_set_my_pwd(self):
        test_pwd = ''.join(random.sample(string.ascii_lowercase, 10))
        new_pwd = self.cat.set_my_pwd(new_pwd=test_pwd)
        self.assertIsNotNone(new_pwd)
        self.assertEqual(new_pwd, test_pwd)
        self.assertEqual(self.cat.password, test_pwd)
        self.cat.password = new_pwd
        self.bkp_cat.password = new_pwd
        new_master_pwd = self.cat.get_master_pwd()
        self.assertIsNotNone(new_master_pwd)

    def test_create_user(self):
        test_user = User(user_name='test_usr12', catalog=self.cat)
        test_pass = 'test_pas12'
        users = self.cat.get_users(names=test_user.user_name)
        if len(users) > 0:
            self.cat.delete(test_user)
        users = self.cat.get_users(names=test_user.user_name)
        self.assertEqual(len(users), 0, msg="Test user exists and I cant delete it")
        self.cat.create_user(username=test_user.user_name, password=test_pass)

        users = self.cat.get_users(names=test_user.user_name)
        self.assertEqual(len(users), 1, msg="Test user was not created")

        tmp_cat = Catalog(service_url=self.cat.service_url, username=test_user.user_name, password=test_pass)
        try:
            tmp_cat.get_users()
        except Exception as e:
            print(f"Some problem with new user, exc: {e}")


    def test_create_existing_user(self):
        test_user = User(user_name='test_usr12', catalog=self.cat)
        test_pass = 'test_pas12'
        self.cat.create_user(username=test_user.user_name, password=test_pass)
        users = self.cat.get_users(names=test_user.user_name)
        self.assertEqual(len(users), 1, msg="User creation before test failed")
        self.cat.create_user(username=test_user.user_name, password=test_pass)


class RolesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cat = Catalog(GSPARAMS['GSURL'], username=GSPARAMS['GSUSER'], password=GSPARAMS['GSPASSWORD'])
        self.test_usr = "test_usr_role"
        self.test_pwd = "test_usr_role"

    def tearDown(self) -> None:
        usr = User(catalog=self.cat, user_name=self.test_usr)
        self.cat.delete(usr)

    def test_get_all_roles(self):
        roles = self.cat.get_roles()
        self.assertGreater(len(roles), 0)
        self.assertIn("ADMIN", roles)

    def test_get_roles_user(self):
        roles = self.cat.get_roles_user(username="admin")
        self.assertGreater(len(roles), 0)
        self.assertIn("ADMIN", roles)

    def test_add_del_role_user(self):
        self.cat.create_user(username=self.test_usr, password=self.test_pwd)
        self.cat.add_role_user(rolename="ADMIN", username=self.test_usr)
        usr_roles = self.cat.get_roles_user(username=self.test_usr)
        self.assertIn("ADMIN", usr_roles)
        tmp_cat = Catalog(service_url=self.cat.service_url, username=self.test_usr, password=self.test_pwd)
        # If role added user should get response for this
        tmp_cat.get_users()
        self.cat.del_role_user(rolename="ADMIN", username=self.test_usr)
        usr_roles = self.cat.get_roles_user(username=self.test_usr)
        self.assertNotIn("ADMIN", usr_roles)








