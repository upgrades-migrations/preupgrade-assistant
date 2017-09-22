from __future__ import unicode_literals
import unittest
import shutil
import os

from preupg import script_api
from preupg.utils import FileHelper
from preupg import settings

try:
    import base
except ImportError:
    import tests.base as base


class TestAPICheck(base.TestCase):

    dirname = os.path.join(os.path.dirname(__file__), 'tmp')
    solution_txt = settings.solution_txt
    api_files = "api_files"
    dist_native = 'dist_native'

    def setUp(self):
        if not os.path.isdir(os.path.join(self.dirname, 'kickstart')):
            os.makedirs(os.path.join(self.dirname, 'kickstart'))
        script_api.VALUE_RPM_RHSIGNED = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_rhsigned')
        script_api.VALUE_RPM_QA = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_qa')
        script_api.VALUE_CHKCONFIG = os.path.join(os.path.dirname(__file__), self.api_files, 'chkconfig')
        script_api.VALUE_CONFIGCHANGED = os.path.join(os.path.dirname(__file__), self.api_files, 'rpm_etc_Va')
        script_api.VALUE_EXECUTABLES = os.path.join(os.path.dirname(__file__), self.api_files, 'executable')
        script_api.PREUPGRADE_CACHE = self.dirname
        script_api.SOLUTION_FILE = self.solution_txt
        if os.environ['XCCDF_VALUE_TMP_PREUPGRADE'] == "":
            script_api.VALUE_TMP_PREUPGRADE = self.dirname

    def test_solution_file(self):
        expected_output = ["Testing message"]
        script_api.solution_file('\n'.join(expected_output))
        output = FileHelper.get_file_content(os.path.join(script_api.VALUE_CURRENT_DIRECTORY, self.solution_txt),
                                             "r",
                                             method=True)
        self.assertEqual(expected_output, output)
        os.unlink(os.path.join(script_api.VALUE_CURRENT_DIRECTORY, self.solution_txt))

    def test_is_pkg_installed(self):
        expected_installed_pkg = "preupgrade-assistant"
        self.assertFalse(script_api.is_pkg_installed("preupgrade-assistant-modules"))
        self.assertTrue(script_api.is_pkg_installed(expected_installed_pkg))

    def test_check_applies_to(self):
        expected_rpms = "foobar,testbar"
        self.assertEqual(script_api.check_applies_to(expected_rpms), 0)

    def test_check_rpm_to(self):
        expected_rpms = "foobar,testbar"
        self.assertEqual(script_api.check_rpm_to(check_rpm=expected_rpms), 0)

    def test_not_check_rpm_to(self):
        expected_rpms = "ffoobar,testbar"
        try:
            self.assertEqual(script_api.check_rpm_to(check_rpm=expected_rpms), 0)
            self.assertTrue(False)
        except SystemExit:
            self.assertTrue(True)

    def test_check_rpm_to_binaries(self):
        expected_binaries = "strings,nm"
        self.assertEqual(script_api.check_rpm_to(check_bin=expected_binaries), 0)

    def test_not_check_rpm_to_binaries(self):
        expected_binaries = "/usr/bin/fooupg,/bin/preupg"
        try:
            self.assertEqual(script_api.check_rpm_to(check_bin=expected_binaries), 0)
            self.assertTrue(False)
        except SystemExit:
            self.assertTrue(True)

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

    def test_deploy_hook_postupgrade(self):
        hook_dir = os.path.join(script_api.VALUE_TMP_PREUPGRADE, "hooks")
        if os.path.isdir(hook_dir):
            shutil.rmtree(hook_dir)
        deploy_type = "postupgrade"
        script_api.deploy_hook(deploy_type, "setup.py", "common.sh", "/usr/bin/nm")
        postupgrade_hook_dir = os.path.join(script_api.VALUE_TMP_PREUPGRADE,
                                            "hooks",
                                            script_api.MODULE_PATH,
                                            deploy_type,
                                            )
        for f in ["run_hook", "common.sh", "nm"]:
            self.assertTrue(os.path.isfile(os.path.join(postupgrade_hook_dir, f)))

    def test_deploy_hook_preupgrade(self):
        hook_dir = os.path.join(script_api.VALUE_TMP_PREUPGRADE, "hooks")
        if os.path.isdir(hook_dir):
            shutil.rmtree(hook_dir)
        deploy_type = "preupgrade"
        script_api.deploy_hook(deploy_type, "setup.py", "common.sh", "/usr/bin/nm")
        preupgrade_hook_dir = os.path.join(script_api.VALUE_TMP_PREUPGRADE,
                                            "hooks",
                                            script_api.MODULE_PATH,
                                            deploy_type,
                                            )
        for f in ["run_hook", "common.sh", "nm"]:
            self.assertTrue(os.path.isfile(os.path.join(preupgrade_hook_dir, f)))


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestAPICheck))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
