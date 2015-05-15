from __future__ import unicode_literals
import unittest
import tempfile
import shutil
# import shlex

import os

from preuputils.compose import XCCDFCompose, ComposeXML
from preuputils import variables
from preup import utils
from preup import settings

FOO_DIR = 'FOOBAR6_7'
FOO_RESULTS = FOO_DIR + variables.result_prefix


class TestContentGenerate(unittest.TestCase):
    def setUp(self):
        self.dir_name = os.path.join(os.getcwd(), 'tests', FOO_DIR, 'dummy')
        self.result_dir = os.path.join(os.getcwd(), 'tests', FOO_RESULTS, 'dummy')

    def tearDown(self):
        shutil.rmtree(os.path.join('tests', FOO_RESULTS))

    def test_compose(self):
        expected_contents = ['failed', 'fixed', 'needs_action', 'needs_inspection', 'not_applicable', 'pass']
        for content in expected_contents:
            compose_xml = ComposeXML()
            result_dir = os.path.join(self.result_dir, content)
            compose_xml.collect_group_xmls(self.dir_name, content=content)
            self.assertTrue(os.path.exists(os.path.join(result_dir, 'group.xml')))
            self.assertFalse(os.path.exists(os.path.join(result_dir, 'all-xccdf.xml')))


class TestGlobalContent(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mktemp(prefix='preupgrade', dir='/tmp')
        self.dir_name = os.path.join(os.getcwd(), 'tests', FOO_DIR)
        self.result_dir = os.path.join(self.temp_dir, FOO_DIR + '-results')
        shutil.copytree(self.dir_name, os.path.join(self.temp_dir, FOO_DIR))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_final_compose(self):
        expected_contents = ['failed', 'fixed', 'needs_action', 'needs_inspection', 'not_applicable', 'pass']
        for content in expected_contents:
            compose_xml = ComposeXML()
            dir_name = os.path.join(self.temp_dir, FOO_DIR, 'dummy')
            compose_xml.collect_group_xmls(dir_name, content=content)

        xccdf_compose = XCCDFCompose(os.path.join(self.temp_dir, FOO_DIR))
        xccdf_compose.generate_xml()
        all_xccdf = os.path.join(self.result_dir, settings.content_file)
        self.assertTrue(os.path.exists(all_xccdf))
        dummy_lines = utils.get_file_content(all_xccdf, 'rb')


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestContentGenerate))
    suite.addTest(loader.loadTestsFromTestCase(TestGlobalContent))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
