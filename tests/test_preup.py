from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preup.application import Application
from preup.conf import Conf, DummyConf
from preup.cli import CLI
from preup import settings, xml_manager
from preup.utils import PostupgradeHelper, SystemIdentification, FileHelper, OpenSCAPHelper
from preup.report_parser import ReportParser

try:
    import base
except ImportError:
    import tests.base as base


def setup_preupg_environment(args, content, tmp_dir, mode=None):
    conf = {
        "contents": content,
        "profile": "xccdf_preupg_profile_default",
        "result_dir": tmp_dir,
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
    a.content = a.conf.contents
    a.basename = os.path.basename(a.content)
    a.openscap_helper = OpenSCAPHelper(a.conf.result_dir,
                                       a.conf.result_name,
                                       a.conf.xml_result_name,
                                       a.conf.html_result_name,
                                       a.content)
    return a


class TestPreupg(base.TestCase):
    temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_dir_name_prefix(self):

        """Basic test for whole program"""

        conf = {
            "contents": "tests/FOOBAR/dummy_preupg/all-xccdf-migrate.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR/dummy_preupg/all-xccdf-migrate.xml"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        a.openscap_helper = OpenSCAPHelper(a.conf.result_dir,
                                           a.conf.result_name,
                                           a.conf.xml_result_name,
                                           a.conf.html_result_name,
                                           a.content)
        self.assertEqual(a.run_scan(), 0)

    def test_dir_name_file(self):

        """Basic test for whole program"""

        conf = {
            "contents": "tests/FOOBAR/dummy_preupg/all-xccdf-migrate.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR/dummy_preupg/all-xccdf-migrate.xml"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        a.openscap_helper = OpenSCAPHelper(a.conf.result_dir,
                                           a.conf.result_name,
                                           a.conf.xml_result_name,
                                           a.conf.html_result_name,
                                           a.content)
        self.assertEqual(a.run_scan(), 0)


class TestPreupgMigrate(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_migrate(self):
        """Basic test for whole program"""

        conf = {
            "contents": "tests/FOOBAR/dummy_preupg/all-xccdf.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
            "mode": 'migrate'
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR/dummy_preupg/all-xccdf-migrate.xml", "--mode", "migrate"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        self.assertEqual(a.run_scan(), 0)
        rp = ReportParser(os.path.join(self.temp_dir, "result.xml"))
        rp.modify_result_path(self.temp_dir, "FOOBAR", 'migrate')
        found_migrate = 0
        found_upgrade = 0
        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            self.assertTrue(values.get("id"))
            if values.get("id").endswith("_state_migrate"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 1)
            if values.get("id").endswith("_state_upgrade"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 0)


class TestPreupg(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_upgrade(self):
        """Basic test for whole program"""

        conf = {
            "contents": "tests/FOOBAR/dummy_preupg/all-xccdf-upgrade.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
            "mode": 'upgrade'
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR/dummy_preupg/all-xccdf-upgrade.xml", "--mode", "upgrade"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        a.openscap_helper = OpenSCAPHelper(a.conf.result_dir,
                                           a.conf.result_name,
                                           a.conf.xml_result_name,
                                           a.conf.html_result_name,
                                           a.content)
        self.assertEqual(a.run_scan(), 0)
        rp = ReportParser(os.path.join(self.temp_dir, "result.xml"))
        rp.modify_result_path(self.temp_dir, "FOOBAR", 'upgrade')
        found_migrate = 0
        found_upgrade = 0
        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            if values.get("id").endswith("_state_migrate"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 0)
            if values.get("id").endswith("_state_upgrade"):
                for value in rp.get_nodes(values, "value"):
                    self.assertEqual(int(value.text), 1)


class TestXMLUpdates(base.TestCase):
    content = "tests/FOOBAR/dummy_preupg/all-xccdf-upgrade.xml"
    test_content = content + ".test"

    def tearDown(self):
        os.remove(self.test_content)

    def test_platform_tag(self):
        shutil.copyfile(self.content, self.test_content)
        rp = ReportParser(self.test_content)
        rp.modify_platform_tag("12")

        found = 0
        for platform in rp.get_nodes(rp.target_tree, "platform"):
            if "cpe:/o:redhat:enterprise_linux:12" in platform.get('idref'):
                found = 1
        self.assertTrue(found)

    def test_result_dirs_tmp_preupgrade(self):
        shutil.copyfile(self.content, self.test_content)
        rp = ReportParser(self.test_content)
        result_path = "/abc/def"
        rp.modify_result_path(result_path, "FOOBAR", 'migrate')
        found_tmp = 0

        for values in rp.get_nodes(rp.target_tree, "Value", ".//"):
            if values.get("id").endswith("_tmp_preupgrade"):
                for value in rp.get_nodes(values, "value"):
                    if value.text == result_path:
                        found_tmp = 1

        self.assertEquals(found_tmp, 1)

    def test_result_dirs_current_dir(self):
        shutil.copyfile(self.content, self.test_content)
        rp = ReportParser(self.test_content)
        result_path = "/abc/efg"
        scenario = 'FOOBAR'
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
            "scan": "FOOBAR",
            "skip_common": False,
            "id": 1,
            "list_contents_set": True,
            "verbose": 1,
            "text": True,
            "contents": "content/FOOBAR",
            "cleanup": True,
            "mode": 'upgrade',
            "select_rules": "abc",
            "list_rules": True,
            "version": True,
            "force": True,
            "riskcheck": True,
            "base_dir": "modules/FOOBAR"
        }
        dc = DummyConf(**conf)
        cli = CLI(["--scan", "FOOBAR", "--skip-common", "--list-contents-set", "--verbose", "--text",
                   "--contents", "content/FOOBAR", "--cleanup", "--mode", "upgrade",
                   "--select-rules", "abc", "--list-rules", "--version", "--force",
                   "--riskcheck", "--base-dir", "modules/FOOBAR"])
        a = Application(Conf(cli.opts, dc, cli))

        self.assertTrue(a.conf.skip_common)
        self.assertEqual(a.conf.contents, "content/FOOBAR")
        self.assertTrue(a.conf.list_contents_set)
        self.assertTrue(a.conf.list_rules)
        self.assertTrue(a.conf.force)
        self.assertTrue(a.conf.text)
        self.assertTrue(a.conf.cleanup)
        self.assertEqual(int(a.conf.verbose), 1)
        self.assertEqual(a.conf.scan, "FOOBAR")
        self.assertEqual(a.conf.mode, "upgrade")
        self.assertEqual(a.conf.select_rules, "abc")
        self.assertTrue(a.conf.riskcheck)
        self.assertEqual(a.conf.base_dir, "modules/FOOBAR")


class TestHashes(base.TestCase):
    dir_name = tempfile.mkdtemp()

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
    extension = "html"

    def test_solution_bold_tag(self):
        solution_text = ['This is solution text [bold: provided as text ] by check script']
        expected_text = ['This is solution text <b> provided as text </b> by check script']
        line = xml_manager.tag_formating(solution_text, self.extension)
        self.assertEqual(expected_text, line)

    def test_solution_www_link_tag(self):
        solution_text = ['This is solution text [link: http://127.0.0.1/all-xccdf.html ] by check script']
        expected_text = ['This is solution text <a href="http://127.0.0.1/all-xccdf.html">http://127.0.0.1/all-xccdf.html</a> by check script']
        line = xml_manager.tag_formating(solution_text, self.extension)
        self.assertEqual(expected_text, line)

    def test_solution_file_link_tag(self):
        solution_text = ['This is solution text [link: description.txt ] by check script']
        expected_text = ['This is solution text <a href="./description.txt">description.txt</a> by check script']
        line = xml_manager.tag_formating(list(solution_text), self.extension)
        self.assertEqual(list(expected_text), line)

    def test_solution_wrong_link_tag(self):
        solution_text = ['This is solution text [link: /var/cache/description.txt] by check script']
        expected_text = ['This is solution text [link: /var/cache/description.txt] by check script']
        line = xml_manager.tag_formating(solution_text, self.extension)
        self.assertEqual(expected_text, line)

    def test_solution_file_bold_tag(self):
        solution_text = ['This is solution text [link: description.txt ] by [bold: check script ]']
        expected_text = ['This is solution text <a href="./description.txt">description.txt</a> by <b> check script </b>']
        line = xml_manager.tag_formating(solution_text, self.extension)
        self.assertEqual(expected_text, line)

    def test_solution_www_bold_tag(self):
        solution_text = ['This is solution text [link: http://127.0.0.1/description.txt ] by [bold: check script ]']
        expected_text = ['This is solution text <a href="http://127.0.0.1/description.txt">http://127.0.0.1/description.txt</a> by <b> check script </b>']
        line = xml_manager.tag_formating(solution_text, self.extension)
        self.assertEqual(expected_text, line)


class TestScenario(base.TestCase):
    temp_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_correct_content_scenario(self):
        """
        Basic test for whole program
        """
        conf = {
            "contents": "tests/FOOBAR/dummy_preupg/all-xccdf.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
            "base_dir": "tests/FOOBAR",
        }

        dir_name = os.path.join("tests", "FOOBAR")
        version_file = os.path.join(dir_name, settings.upgrade_version_file)
        FileHelper.write_to_file(version_file, "w", ['6_7'],)
        dc = DummyConf(**conf)
        cli = CLI(["--contents", os.path.join(dir_name, "dummy_preupg/all-xccdf.xml")])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        self.assertEqual(a.get_scenario(), "FOOBAR")
        if os.path.exists(version_file):
            os.unlink(version_file)

    def test_scenario_without_version_file(self):
        """
        Basic test for whole program
        """
        conf = {
            "contents": "tests/FOOBAR_A/dummy_preupg/all-xccdf.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
            "base_dir": "tests/FOOBAR_A",
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR_A/dummy_preupg/all-xccdf.xml"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        self.assertEqual(a.get_scenario(), None)

    def test_scenario_with_wrong_version_file(self):
        """
        Basic test for whole program
        """
        conf = {
            "contents": "tests/FOOBAR_A/dummy_preupg/all-xccdf.xml",
            "profile": "xccdf_preupg_profile_default",
            "result_dir": self.temp_dir,
            "skip_common": True,
            "temp_dir": self.temp_dir,
            "id": None,
            "debug": True,  # so root check won't fail
            "base_dir": "tests/FOOBAR_A",
        }

        dir_name = os.path.join("tests", "FOOBAR")
        version_file = os.path.join(dir_name, settings.upgrade_version_file)
        FileHelper.write_to_file(version_file, "w", ['6_7'],)
        dc = DummyConf(**conf)
        cli = CLI(["--contents", "tests/FOOBAR_A/dummy_preupg/all-xccdf.xml"])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        self.assertEqual(a.get_scenario(), None)
        if os.path.exists(version_file):
            os.unlink(version_file)


class TestPreupgradeVersion(base.TestCase):
    def setUp(self):
        settings.prefix = 'preupgrade'

    def test_correct_version(self):

        version = SystemIdentification.check_version(['6_7'])
        self.assertEqual(version, ['6', '7'])

    def test_wrong_version(self):
        version = SystemIdentification.check_version(['7_6'])
        self.assertEqual(version, False)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # TODO We have to find out a diferent way how to test it.
    # TODO oscap does not support --progress option
    #suite.addTest(loader.loadTestsFromTestCase(TestPreupg))
    #suite.addTest(loader.loadTestsFromTestCase(TestPreupgMigrate))
    #suite.addTest(loader.loadTestsFromTestCase(TestPreupgUpgrade))
    suite.addTest(loader.loadTestsFromTestCase(TestCLI))
    suite.addTest(loader.loadTestsFromTestCase(TestHashes))
    suite.addTest(loader.loadTestsFromTestCase(TestSolutionReplacement))
    suite.addTest(loader.loadTestsFromTestCase(TestXMLUpdates))
    suite.addTest(loader.loadTestsFromTestCase(TestScenario))
    suite.addTest(loader.loadTestsFromTestCase(TestPreupgradeVersion))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
