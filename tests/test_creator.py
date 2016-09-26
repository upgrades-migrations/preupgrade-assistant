
from __future__ import unicode_literals, print_function
import unittest
import tempfile
import os
import shutil

try:
    import base
except ImportError:
    import tests.base as base

from preup.creator.ui_helper import UIHelper
from preup.utils import FileHelper


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
    content_name = "foobar_content"

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.upgrade_dir = os.path.join(self.tempdir, "FOOBAR6_7")
        os.makedirs(self.upgrade_dir)
        self.puh = UIHelper(self.upgrade_dir)
        self.puh._group_name = self.group_name
        self.puh._content_name = self.content_name
        self.puh.check_script = True
        self.puh.solution_file = True
        self.puh.script_type = "sh"
        content_dict = {}
        content_dict['check_script'] = "foobar_check_script.sh"
        content_dict['solution'] = "foobar_solution.txt"
        content_dict['content_title'] = "foobar_test_title"
        content_dict['content_description'] = "Foobar content test description"
        self.puh.content_dict = content_dict
        self.puh.content_path = os.path.join(self.puh.get_group_name(), self.puh.get_content_name())
        if os.path.exists(self.puh.get_content_path()):
            shutil.rmtree(self.puh.get_content_path())
        os.makedirs(self.puh.get_content_path())
        self.puh.prepare_content_env()
        self.puh.create_final_content()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_content_ini(self):
        content_ini = os.path.join(self.puh.get_content_path(), self.puh.get_content_ini_file())
        self.assertEqual(content_ini, os.path.join(self.upgrade_dir,
                                                   self.group_name,
                                                   self.content_name,
                                                   self.content_name + '.ini'))
        lines = load_file(content_ini)
        expected_ini = ['[preupgrade]',
                        'check_script = foobar_check_script.sh',
                        'content_description = Foobar content test description',
                        'solution = foobar_solution.txt',
                        'content_title = foobar_test_title',
                        '']

        self.assertEqual(lines, expected_ini)

    def test_group_ini(self):
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

    def test_check_script(self):
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


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestCreator))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
