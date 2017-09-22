from __future__ import unicode_literals, print_function
import unittest
import tempfile
import os
import shutil
import ConfigParser

try:
    import base
except ImportError:
    import tests.base as base

from preupg import settings
from preupg.creator import ui_helper
from preupg.creator.ui_helper import UIHelper
from preupg.utils import FileHelper


def load_file(filename):
    try:
        lines = FileHelper.get_file_content(filename, "rb", True)
        lines = [x.strip() for x in lines]
    except IOError:
        assert False
    return lines


class TestCreator(base.TestCase):

    tempdir = ""
    upgrade_dir = ""
    puh = None
    group_name = "foobar_group"
    content_name = settings.module_ini
    content_dict = {}

    class Identity(base.MockFunction):
        def __init__(self, identity):
            self.identity = identity

        def __call__(self, *args, **kwargs):
            return self.identity

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.upgrade_dir = os.path.join(self.tempdir, "FOOBAR6_7")
        os.makedirs(self.upgrade_dir)
        self.puh = UIHelper(self.upgrade_dir)
        self.puh._group_name = self.group_name
        self.puh._content_name = self.content_name
        self.puh.check_script = True
        self.puh.solution_file = True
        self.content_dict['content_title'] = "foobar_test_title"
        self.content_dict['content_description'] = "Foobar content test description"
        self.puh.content_dict = self.content_dict
        self.puh.content_path = os.path.join(self.puh.get_group_name(), self.puh.get_content_name())
        if os.path.exists(self.puh.get_content_path()):
            shutil.rmtree(self.puh.get_content_path())
        os.makedirs(self.puh.get_content_path())

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @base.mock(UIHelper, "properties_ini_exists", Identity(True))
    def test_content_ini(self):
        self.puh.script_type = "sh"
        self.puh.prepare_content_env()
        self.puh.create_final_content()
        content_ini = os.path.join(self.puh.get_content_path(),
                                   self.puh.get_content_ini_file())
        self.assertEqual(content_ini, os.path.join(self.upgrade_dir,
                                                   self.group_name,
                                                   self.content_name,
                                                   self.content_name))
        lines = load_file(content_ini)
        expected_ini = ['[preupgrade]',
                        'content_description = Foobar content test description',
                        'content_title = foobar_test_title',
                        '']
        self.assertEqual(expected_ini.sort(), lines.sort())

    @base.mock(UIHelper, "properties_ini_exists", Identity(True))
    def test_group_ini(self):
        self.puh.script_type = "sh"
        self.puh.prepare_content_env()
        self.puh.create_final_content()
        group_ini = os.path.join(self.puh.get_upgrade_path(),
                                 self.puh.get_group_name(), 'group.ini')
        self.assertEqual(group_ini, os.path.join(self.upgrade_dir,
                                                 self.group_name,
                                                 'group.ini'))
        lines = load_file(group_ini)
        expected_group_ini = ['[preupgrade]',
                              'group_title = Title for foobar_group',
                              '']
        self.assertEqual(lines, expected_group_ini)

    @base.mock(UIHelper, "properties_ini_exists", Identity(True))
    def test_bash_check_script(self):
        self.puh.script_type = "sh"
        self.puh.prepare_content_env()
        self.puh.create_final_content()
        check_script = os.path.join(self.puh.get_content_path(), self.puh.get_check_script())
        lines = load_file(check_script)
        exp_script = ['#!/bin/bash',
                      '',
                      '. /usr/share/preupgrade/common.sh',
                      '',
                      '#END GENERATED SECTION',
                      '',
                      "### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.",
                      '']
        self.assertEqual(lines, exp_script)

    @base.mock(UIHelper, "properties_ini_exists", Identity(True))
    def test_python_check_script(self):
        self.puh.script_type = "python"
        self.puh.prepare_content_env()
        self.puh.create_final_content()
        check_script = os.path.join(self.puh.get_content_path(), self.puh.get_check_script())
        lines = load_file(check_script)
        exp_script = ['#!/usr/bin/python',
                      '# -*- Mode: Python; python-indent: 8; indent-tabs-mode: t -*-', '',
                      'import sys',
                      'import os', '',
                      'from preupg.script_api import *', '',
                      '#END GENERATED SECTION', '',
                      "### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'."]
        self.assertTrue(exp_script, lines)

    @base.mock(UIHelper, "properties_ini_exists", Identity(False))
    def test_create_properties_ini(self):
        """ Create valid properties.ini file """
        ini_content = ["[preupgrade-assistant-modules]",
                       "src_major_version = 6",
                       "dst_major_version = 7",
                       ""]

        ui = UIHelper()
        ui.src_version = 6
        ui.dst_version = 7

        tmp_file_name = tempfile.mkstemp()[1]
        ui.properties_ini_path = tmp_file_name
        ui.create_properties_ini()
        tmp_content = load_file(tmp_file_name)
        self.assertEqual(tmp_content, ini_content)
        os.remove(tmp_file_name)

    @base.mock(UIHelper, "check_path", Identity(True))
    def test_specify_upgrade_path(self):
        """Normal pass"""
        self.assertTrue(self.puh.specify_upgrade_path())

    def test_is_valid_string(self):
        self.assertTrue(UIHelper.is_valid_string('text'))
        self.assertTrue(UIHelper.is_valid_string(u'text'))

        self.assertFalse(UIHelper.is_valid_string(""))
        self.assertFalse(UIHelper.is_valid_string(None))
        self.assertFalse(UIHelper.is_valid_string(0))

    @base.mock(ui_helper, "get_user_input", Identity('6'))
    def test_ask_about_version_number(self):
        self.assertEqual(UIHelper.ask_for_string(
            "msg", "err_msg"), '6')

    @base.mock(ui_helper, "get_user_input", Identity(''))
    def test_ask_about_wrong_version(self):
        self.assertEqual(UIHelper.ask_for_string(
            "msg", "err_msg"), False)

    def test_write_config_to_file(self):
        """ Test creation and content in config file """
        config = ConfigParser.RawConfigParser()
        section = "section"
        config.add_section(section)
        config.set(section, 'option', 'value')

        tmp_file_name = tempfile.mkstemp()[1]
        UIHelper.write_config_to_file(tmp_file_name, config)
        tmp_content = load_file(tmp_file_name)
        expected_content = ['[section]', 'option = value', '']
        self.assertEqual(tmp_content, expected_content)
        os.remove(tmp_file_name)

    def test_write_config_to_nofile(self):
        """ Write config to non-existing file path """
        self.assertRaises(IOError, UIHelper.write_config_to_file, '', None)


def suite():
    loader = unittest.TestLoader()
    unit_suite = unittest.TestSuite()
    unit_suite.addTest(loader.loadTestsFromTestCase(TestCreator))
    return unit_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
