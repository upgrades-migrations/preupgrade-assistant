from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os
from glob import glob

from preupg.xmlgen.compose import XCCDFCompose, ComposeXML
from preupg.utils import FileHelper
from preupg import settings

try:
    import base
except ImportError:
    import tests.base as base

FOO_DIR = 'FOOBAR6_7'
FOO_RESULTS = FOO_DIR + settings.results_postfix


class TestContentGenerate(base.TestCase):
    dir_name = None
    result_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='preupgrade', dir='/tmp')
        self.dir_name = os.path.join(os.getcwd(), 'tests', FOO_DIR)
        self.result_dir = os.path.join(self.temp_dir, 'tests', FOO_RESULTS)
        shutil.copytree(self.dir_name, os.path.join(self.temp_dir, FOO_DIR))
        self.dir_name = os.path.join(self.temp_dir, FOO_DIR)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        for d, subd, file_name in os.walk(self.dir_name):
            group_xml = [x for x in file_name if x == 'group.xml']
            if group_xml:
                os.unlink(os.path.join(d, group_xml[0]))

    def test_compose(self):
        ComposeXML().collect_group_xmls(self.dir_name, self.dir_name)
        for subdir in glob(os.path.join(self.dir_name, "*/")):
            self.assertTrue(os.path.exists(os.path.join(subdir, 'group.xml')))
            self.assertFalse(os.path.exists(
                os.path.join(subdir, settings.all_xccdf_xml_filename)))


class TestGlobalContent(base.TestCase):
    temp_dir = None
    dir_name = None
    result_dir = None

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='preupgrade', dir='/tmp')
        self.dir_name = os.path.join(os.getcwd(), 'tests', FOO_DIR)
        self.result_dir = os.path.join(self.temp_dir, FOO_DIR + '-results')
        shutil.copytree(self.dir_name, os.path.join(self.temp_dir, FOO_DIR))
        self.data_dir_orig = settings.data_dir
        settings.data_dir = os.path.join(os.getcwd(), "data")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        settings.data_dir = self.data_dir_orig

    def test_final_compose(self):
        dir_name = os.path.join(self.temp_dir, FOO_DIR)
        ComposeXML().collect_group_xmls(dir_name, dir_name)

        xccdf_compose = XCCDFCompose(os.path.join(self.temp_dir, FOO_DIR))
        xccdf_compose.generate_xml()
        all_xccdf = os.path.join(self.result_dir,
                                 settings.all_xccdf_xml_filename)
        self.assertTrue(os.path.exists(all_xccdf))
        dummy_lines = FileHelper.get_file_content(all_xccdf, 'rb')


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestContentGenerate))
    suite.addTest(loader.loadTestsFromTestCase(TestGlobalContent))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
