from __future__ import unicode_literals
import unittest
import shutil
import os

from preup import script_api
from preup.utils import FileHelper

try:
    import base
except ImportError:
    import tests.base as base


class TestAPICheck(base.TestCase):

    dirname = os.path.join(os.path.dirname(__file__), 'tmp')
    solution_txt = 'solution.txt'
    api_files = "api_files"
    dist_native = 'dist_native'

    def setUp(self):
        if os.path.isdir(self.dirname):
            shutil.rmtree(self.dirname)
        os.makedirs(self.dirname)
        os.makedirs(os.path.join(self.dirname, 'kickstart'))
        script_api.VALUE_RPM_RHSIGNED = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_rhsigned.log')
        script_api.VALUE_RPM_QA = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_qa.log')
        script_api.VALUE_CHKCONFIG = os.path.join(os.path.dirname(__file__), self.api_files, 'chkconfig.log')
        script_api.VALUE_CONFIGCHANGED = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_etc_Va.log')
        script_api.PREUPGRADE_CACHE = self.dirname
        script_api.SOLUTION_FILE = self.solution_txt

    def test_solution_file(self):
        expected_output = ["Testing message"]
        script_api.solution_file('\n'.join(expected_output))
        output = FileHelper.get_file_content(os.path.join(self.dirname, self.solution_txt), "r", method=True)
        self.assertEqual(expected_output, output)

    def test_is_pkg_installed(self):
        expected_installed_pkg = "preupgrade-assistant"
        self.assertFalse(script_api.is_pkg_installed("preupgrade-assistant-modules"))
        self.assertTrue(script_api.is_pkg_installed(expected_installed_pkg))

    def test_check_applies_to(self):
        expected_rpms = "foobar,testbar"
        self.assertEqual(script_api.check_applies_to(expected_rpms), 0)

    def test_check_rpm_to(self):
        expected_rpms = "foobar,testbar"
        expected_binaries = "/usr/bin/evince,/usr/bin/expr"
        self.assertEqual(script_api.check_rpm_to(expected_rpms, expected_binaries), 0)

    def test_service_is_enabled(self):
        expected_service_enabled = "foo"
        expected_service_disabled = "foonetwork"
        self.assertTrue(script_api.service_is_enabled(expected_service_enabled))
        self.assertFalse(script_api.service_is_enabled(expected_service_disabled))

    def test_config_file_changed(self):
        self.assertTrue(script_api.config_file_changed("/etc/foo/test.conf"))
        self.assertFalse(script_api.config_file_changed("/etc/foobar/test.conf"))

    def test_is_dist_native(self):
        self.assertTrue(script_api.is_dist_native('foobar'))
        script_api.DEVEL_MODE = 1
        script_api.DIST_NATIVE = "all"
        self.assertTrue(script_api.is_dist_native("preupgrade-assistant"))
        script_api.DIST_NATIVE = "sign"
        self.assertFalse(script_api.is_dist_native("preupgrade-assistant"))
        script_api.DIST_NATIVE = os.path.join(os.path.dirname(__file__), self.api_files, self.dist_native)
        self.assertFalse(script_api.is_dist_native("non-sense"))

    def test_get_dist_native_list(self):
        expected_list = ['foobar',
                         'barfoo',
                         'testbar',
                         'footest']
        self.assertEqual(script_api.get_dist_native_list(), expected_list)

    def test_add_pkg_to_kickstart(self):
        expected_list = ['my_foo_pkg', 'my_bar_pkg']
        script_api.add_pkg_to_kickstart(['my_foo_pkg', 'my_bar_pkg'])
        for pkg in FileHelper.get_file_content(script_api.SPECIAL_PKG_LIST, 'rb', method=True):
            self.assertTrue(pkg.strip() in expected_list)
        script_api.add_pkg_to_kickstart('my_foo_pkg my_bar_pkg')
        for pkg in FileHelper.get_file_content(script_api.SPECIAL_PKG_LIST,'rb', method=True):
            self.assertTrue(pkg.strip() in expected_list)

    def tearDown(self):
        if os.path.isdir(self.dirname):
            shutil.rmtree(self.dirname)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestAPICheck))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
