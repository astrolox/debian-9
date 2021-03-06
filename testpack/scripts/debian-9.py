#!/usr/bin/env python3

import unittest
import os
import docker
import json
import subprocess
from stat import *


class Test1and1BaseImage(unittest.TestCase):
    docker_client = None
    docker_container = None

    @classmethod
    def setUpClass(cls):
        image_to_test = os.getenv("IMAGE_NAME")
        if image_to_test == "":
            raise Exception("I don't know what image to test")
        Test1and1BaseImage.docker_client = docker.from_env()
        Test1and1BaseImage.container = Test1and1BaseImage.docker_client.containers.run(
            image=image_to_test,
            remove=True,
            detach=True
        )

    @classmethod
    def tearDownClass(cls):
        Test1and1BaseImage.container.stop()

    def setUp(self):
        print ("\nIn method", self._testMethodName)
        self.container = Test1and1BaseImage.container

    def execRun(self, command):
        return self.container.exec_run(command).decode('utf-8')

    def assertPackageIsInstalled(self, packageName):
        op = self.execRun("dpkg -l %s" % packageName)
        self.assertTrue(
            op.find(packageName) > -1,
            msg="%s package not installed" % packageName
        )

    # <tests to run>

    def test_docker_logs(self):
        expected_log_lines = [
            "run-parts: executing /hooks/entrypoint-pre.d/00_check_euid",
            "run-parts: executing /hooks/entrypoint-pre.d/01_ssmtp_setup",
            "run-parts: executing /hooks/entrypoint-pre.d/02_user_group_setup",
            "run-parts: executing /hooks/supervisord-pre.d/20_configurability"
        ]
        container_logs = self.container.logs().decode('utf-8')
        for expected_log_line in expected_log_lines:
            self.assertTrue(
                container_logs.find(expected_log_line) > -1,
                msg="Docker log line missing: %s from (%s)" % (expected_log_line, container_logs)
            )

    def test_OS(self):
        lines = self.execRun("cat /etc/debian_version")
        self.assertTrue(lines.find("9.") > -1, msg="Failed to establish correct version")

    def test_id(self):
        self.assertEqual("root", self.execRun("whoami")[:-1])

    def test_supervisor(self):
        self.assertPackageIsInstalled("supervisor")

        self.assertTrue(
            self.execRun("ps -ef").find('supervisord') > -1,
            msg="supervisord not running"
        )

        self.assertFalse(
            self.execRun("ls -l /etc/supervisor/supervisord.conf").find("No such file or directory") > -1,
            msg="/etc/supervisor/supervisord.conf is missing"
        )

    def test_vim(self):
        self.assertPackageIsInstalled("vim")

    def test_curl(self):
        self.assertPackageIsInstalled("curl")

    def test_bzip2(self):
        self.assertPackageIsInstalled("bzip2")

    def test_apt(self):
        self.assertTrue(
            self.execRun("ls -l /var/lib/apt/lists").find("total 0") > -1,
            msg="/var/lib/apt/lists should be empty"
        )

    # </tests to run>

if __name__ == '__main__':
    unittest.main(verbosity=1)
