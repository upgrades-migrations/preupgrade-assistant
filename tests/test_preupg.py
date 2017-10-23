from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preupg.application import Application
from preupg.conf import Conf, DummyConf
from preupg.cli import CLI
from preupg import settings, xml_manager
from preupg.utils import (PostupgradeHelper, FileHelper,
                          OpenSCAPHelper, ModuleSetUtils)
from preupg.report_parser import ReportParser

try:
    import base
except ImportError:
    import tests.base as base


def setup_preupg_environment(args, content, tmp_dir, mode=None):
    conf = {
        "contents": content,
        "profile": "xccdf_preupg_profile_default",
        "assessment_results_dir": tmp_dir,
        "skip_common": True,
        "temp_dir": tmp_dir,
        "id": None,
        "debug": True,  # so root check won't fail
        "mode": mode,
    }
    dc = DummyConf(**conf)
    cli = CLI(args)
    a = Application(Conf(dc, settings, cli))
    # Prepare all variables for test
    a.conf.source_dir = os.getcwd()
    a.determine_module_set_location()
    a.openscap_helper = OpenSCAPHelper(a.conf.assessment_results_dir,
                                       a.conf.result_prefix,
                                       a.conf.xml_result_name,
                                       a.conf.html_result_name,
                                       a.all_xccdf_xml_path)
    return a


class TestPreupg(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_all(self):

        """Basic test for whole program"""

        content = "tests/generated_results/all-xccdf-migrate.xml"
        args = ["--contents", content]
        a = setup_preupg_environment(args, content, self.temp_dir)
        self.assertEqual(a.run_scan(), 0)


class TestPreupgMigrate(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_migrate(self):
        """Basic test for whole program"""

        content = "tests/generated_results/all-xccdf-migrate.xml"
        args = ["--contents", content, "--mode", "migrate"]
        a = setup_preupg_environment(args, content, self.temp_dir, mode='migrate')
        self.assertEqual(a.run_scan(), 0)
        rp = ReportParser(os.path.join(self.temp_dir,
                                       settings.xml_result_name))
        rp.modify_result_path(self.temp_dir, "FOOBAR6_7", 'migrate')
        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            self.assertTrue(values.get("id"))
            if values.get("id").endswith("_state_migrate"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 1)
            if values.get("id").endswith("_state_upgrade"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 0)


class TestPreupgUpgrade(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_upgrade(self):
        """Basic test for whole program"""

        content = "tests/generated_results/all-xccdf-upgrade.xml"
        args = ["--contents", content, "--mode", "upgrade"]
        a = setup_preupg_environment(args, content, self.temp_dir, mode='upgrade')
        self.assertEqual(a.run_scan(), 0)
        rp = ReportParser(os.path.join(self.temp_dir, "result.xml"))
        rp.modify_result_path(self.temp_dir, "FOOBAR6_7", 'upgrade')
        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            if values.get("id").endswith("_state_migrate"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 0)
            if values.get("id").endswith("_state_upgrade"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 1)


class TestXMLUpdates(base.TestCase):
    content = None
    test_content = None

    def setUp(self):
        self.content = "tests/generated_results/all-xccdf-upgrade.xml"
        self.test_content = self.content+".test"

    def tearDown(self):
        os.remove(self.test_content)

    def test_result_dirs_tmp_preupgrade(self):
        shutil.copyfile(self.content, self.test_content)
        rp = ReportParser(self.test_content)
        result_path = "/abc/def"
        rp.modify_result_path(result_path, "FOOBAR6_7", 'migrate')
        found_tmp = 0

        for values in rp.get_nodes(rp.target_tree, "Value", prefix='./'):
            if values.get("id").endswith("_tmp_preupgrade"):
                for value in rp.get_nodes(values, "value"):
                    if value.text == result_path:
                        found_tmp = 1

        self.assertEquals(found_tmp, 1)

    def test_result_dirs_current_dir(self):
        shutil.copyfile(self.content, self.test_content)
        rp = ReportParser(self.test_content)
        result_path = "/abc/efg"
        scenario = 'FOOBAR6_7'
        rp.modify_result_path(result_path, scenario, 'migrate')
        found_current = 0
        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            if values.get("id").endswith("_preupg_state_current_directory"):
                for value in rp.get_nodes(values, "value"):
                    result_dir = result_path+"/"+scenario+"/dummy_preupg"
                    if value.text == result_dir:
                        found_current = 1

        self.assertEquals(found_current, 1)


class TestCLI(base.TestCase):
    def test_opts(self):
        """ basic test of several options """
        conf = {
            "scan": "FOOBAR6_7",
            "skip_common": False,
            "id": 1,
            "list_contents_set": True,
            "verbose": 1,
            "text": True,
            "contents": "content/FOOBAR6_7",
            "cleanup": True,
            "mode": 'upgrade',
            "select_rules": "abc",
            "list_rules": True,
            "version": True,
            "force": True,
            "riskcheck": True,
        }
        dc = DummyConf(**conf)
        cli = CLI(["--scan", "FOOBAR6_7", "--skip-common", "--cleanup",
                   "--list-contents-set", "--verbose", "--text", "--force",
                   "--mode", "upgrade", "--select-rules", "abc", "--riskcheck",
                   "--list-rules"])
        a = Application(Conf(cli.opts, dc, cli))

        self.assertTrue(a.conf.skip_common)
        self.assertEqual(a.conf.contents, "content/FOOBAR6_7")
        self.assertTrue(a.conf.list_contents_set)
        self.assertTrue(a.conf.list_rules)
        self.assertTrue(a.conf.force)
        self.assertTrue(a.conf.text)
        self.assertTrue(a.conf.cleanup)
        self.assertEqual(int(a.conf.verbose), 1)
        self.assertEqual(a.conf.scan, "FOOBAR6_7")
        self.assertEqual(a.conf.mode, "upgrade")
        self.assertEqual(a.conf.select_rules, "abc")
        self.assertTrue(a.conf.riskcheck)


class TestHashes(base.TestCase):
    dir_name = None

    def setUp(self):
        self.dir_name = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test_hashes(self):
        text_to_hash="""
            This is preupgrade assistant test has string"
        """
        self.dir_name = "tests/hashes"
        os.mkdir(self.dir_name)
        FileHelper.write_to_file(os.path.join(self.dir_name, "post_script"), 'wb', text_to_hash)
        PostupgradeHelper.hash_postupgrade_file(False, self.dir_name)
        return_value = PostupgradeHelper.hash_postupgrade_file(False, self.dir_name, check=True)
        self.assertTrue(return_value)


class TestSolutionReplacement(base.TestCase):

    def test_solution_bold_tag(self):
        solution_text = 'This is solution text [bold: provided as text ] by check script'
        expected_text = 'This is solution text <b> provided as text </b> by check script'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)

    def test_solution_www_link_tag(self):
        solution_text = 'This is solution text [link: http://127.0.0.1/all-xccdf.html ] by check script'
        expected_text = 'This is solution text <a href="http://127.0.0.1/all-xccdf.html">http://127.0.0.1/all-xccdf.html</a> by check script'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)

    def test_solution_file_link_tag(self):
        solution_text = 'This is solution text [link: description.txt ] by check script'
        expected_text = 'This is solution text <a href="./description.txt">description.txt</a> by check script'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)

    def test_solution_wrong_link_tag(self):
        solution_text = 'This is solution text [link: /var/cache/description.txt] by check script'
        expected_text = 'This is solution text /var/cache/description.txt by check script'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)

    def test_solution_file_bold_tag(self):
        solution_text = 'This is solution text [link: description.txt ] by [bold: check script ]'
        expected_text = 'This is solution text <a href="./description.txt">description.txt</a> by <b> check script </b>'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)

    def test_solution_www_bold_tag(self):
        solution_text = 'This is solution text [link: http://127.0.0.1/description.txt ] by [bold: check script ]'
        expected_text = 'This is solution text <a href="http://127.0.0.1/description.txt">http://127.0.0.1/description.txt</a> by <b> check script </b>'
        line = xml_manager.tag_formating(solution_text)
        self.assertEqual(expected_text, line)


class TestModuleSet(base.TestCase):
    '''
    Test get_scenario method, to get directory with modules
    '''
    def test_correct_module_set(self):
        '''
        Test to get right module directory with contents option,
        directory with modules are the same where all-xccdf file is located
        '''
        conf = {
            "contents": "tests/Modules/all-xccdf.xml",
        }
        dummy_conf = DummyConf(**conf)
        cli = CLI(["--contents", "tests/Modules/all-xccdf.xml"])
        app = Application(Conf(dummy_conf, settings, cli))
        # Prepare all variables for test
        app.conf.source_dir = os.getcwd()
        app.content = app.conf.contents
        app.basename = os.path.basename(app.content)
        app.determine_module_set_location()
        self.assertEqual(app.module_set_dirname, 'Modules')


class TestModuleSetConfigParse(base.TestCase):
    '''
    Test parser of source and destination major versions of system from module
    set config file
    '''
    def test_valid_config(self):
        '''
        Test check if parse on correct module set config works fine
        '''
        this_file_dir_path = os.path.dirname(os.path.realpath(__file__))
        dummy_config_path = os.path.join(this_file_dir_path, 'FOOBAR6_7')
        version = ModuleSetUtils.get_module_set_os_versions(dummy_config_path)
        self.assertEqual(version, ['6', '7'])

    def test_invalid_config(self):
        '''
        Test with wrong module set config path
        '''
        self.assertRaises(EnvironmentError,
                          ModuleSetUtils.get_module_set_os_versions,
                          '/dev/null')


class TestModuleSetConfigContent(base.TestCase):
    '''
    Test case for validation keys and sections inside module set config file
    '''
    def __init__(self, *args, **kwargs):
        super(TestModuleSetConfigContent, self).__init__(*args, **kwargs)
        self.src_version_key = "src_major_version"
        self.dst_version_key = "dst_major_version"
        self.section_name = "preupgrade-assistant-modules"
        self.this_file_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.dummy_config_path = os.path.join(self.this_file_dir_path,
                                              'FOOBAR6_7/properties.ini')

    def test_valid_keys(self):
        '''
        Test to check correct valid keys in module set config file
        '''
        try:
            for key in [self.src_version_key, self.dst_version_key]:
                ModuleSetUtils.get_config_key_value(self.dummy_config_path,
                                                    key,
                                                    self.section_name)
        except EnvironmentError:
            self.fail('Key: {0} in {1} file should be correct'.format(
                self.src_version_key, self.dummy_config_path))

    def test_invalid_key(self):
        '''
        Test to check some invalid non existing key in module set config file
        '''
        self.assertRaises(EnvironmentError,
                          ModuleSetUtils.get_config_key_value,
                          self.dummy_config_path, "invalid_key",
                          self.section_name)

    def test_invalid_section(self):
        '''
        Test to check some invalid non existing section in module set config
        file
        '''
        self.assertRaises(EnvironmentError,
                          ModuleSetUtils.get_config_key_value,
                          self.dummy_config_path, self.src_version_key,
                          "invalid_section")


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPreupg))
    suite.addTest(loader.loadTestsFromTestCase(TestPreupgMigrate))
    suite.addTest(loader.loadTestsFromTestCase(TestPreupgUpgrade))
    suite.addTest(loader.loadTestsFromTestCase(TestCLI))
    suite.addTest(loader.loadTestsFromTestCase(TestHashes))
    suite.addTest(loader.loadTestsFromTestCase(TestSolutionReplacement))
    suite.addTest(loader.loadTestsFromTestCase(TestXMLUpdates))
    suite.addTest(loader.loadTestsFromTestCase(TestModuleSet))
    suite.addTest(loader.loadTestsFromTestCase(TestModuleSetConfigParse))
    suite.addTest(loader.loadTestsFromTestCase(TestModuleSetConfigContent))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
