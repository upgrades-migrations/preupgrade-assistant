from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preup import xccdf
from preup import utils
from preup.conf import Conf, DummyConf
from preup.cli import CLI
from preup.application import Application
from preup import settings


class TestRiskCheck(unittest.TestCase):

    def _generate_result(self, content_temp):
        conf = {
            "contents": content_temp,
            "profile": "xccdf_preupg_profile_default",
            "result_dir": os.path.dirname(content_temp),
            "skip_common": True,
            "temp_dir": os.path.dirname(content_temp),
            "id": None,
            "debug": True,  # so root check won't fail
        }

        dc = DummyConf(**conf)
        cli = CLI(["--contents", content_temp])
        a = Application(Conf(dc, settings, cli))
        # Prepare all variables for test
        a.conf.source_dir = os.getcwd()
        a.content = a.conf.contents
        a.basename = os.path.basename(a.content)
        self.assertEqual(a.run_scan(), 0)

    def _copy_xccdf_file(self, update_text):
        temp_dir = tempfile.mkdtemp()
        xccdf_file = os.path.join(os.getcwd(), 'tests', 'FOOBAR6_7', 'dummy_preupg', 'all-xccdf.xml')
        temp_file = os.path.join(temp_dir, 'all_xccdf.xml')
        shutil.copyfile(xccdf_file, temp_file)
        content = utils.get_file_content(temp_file, 'rb', decode_flag=False)
        content = content.replace(b'INPLACE_TAG', update_text)
        utils.write_to_file(temp_file, 'wb', content)
        return temp_file

    def test_check_inplace_risk_high(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: HIGH: Test High Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, 1)

    def test_check_inplace_risk_medium(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: MEDIUM: Test Medium Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, 1)

    def test_check_inplace_risk_slight(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: SLIGHT: Test Slight Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, 0)

    def test_check_inplace_risk_none(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: NONE: Test None Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, 0)

    def test_check_inplace_risk_extreme(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: EXTREME: Test Extreme Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, 2)

    def test_check_inplace_risk_unknown(self):

        temp_file = self._copy_xccdf_file(b'INPLACERISK: UNKNOWN: Test Extreme Inplace risk')
        self._generate_result(temp_file)
        return_value = xccdf.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'result.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        self.assertEqual(return_value, -1)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestRiskCheck))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
