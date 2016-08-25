from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preup.xccdf import XccdfHelper
from preup.utils import FileHelper
from preup.conf import Conf, DummyConf
from preup.cli import CLI
from preup.application import Application
from preup import settings
from preup.utils import OpenSCAPHelper

try:
    import base
except ImportError:
    import tests.base as base


class TestRiskCheck(base.TestCase):

    risks = ['SLIGHT', 'MEDIUM', 'HIGH', 'EXTREME']

    def _copy_xccdf_file(self, update_text=None, update_return_value=None):
        temp_dir = tempfile.mkdtemp()
        xccdf_file = os.path.join(os.getcwd(), 'tests', 'generated_results', 'inplace_risk_test.xml')
        temp_file = os.path.join(temp_dir, 'all-xccdf.xml')
        shutil.copyfile(xccdf_file, temp_file)
        content = FileHelper.get_file_content(temp_file, 'rb', decode_flag=False)
        new_text = b'preupg.risk.%s: Test %s Inplace risk' % (update_text, update_text)
        if update_text is not None:
            content = content.replace(b'INPLACE_TAG', new_text)
        else:
            content = content.replace(b'INPLACE_TAG', "")
        content = content.replace(b'RESULT_VALUE', update_return_value)
        FileHelper.write_to_file(temp_file, 'wb', content)
        return temp_file

    def _update_xccdf_file(self, return_value, risk):
        temp_file = self._copy_xccdf_file(update_return_value=return_value,
                                          update_text=risk)
        return_value = XccdfHelper.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'all-xccdf.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        return return_value

    def test_check_inplace_risk_high(self):
        self.assertEqual(self._update_xccdf_file('needs_action', 'HIGH'), 1)

    def test_check_inplace_risk_medium(self):
        self.assertEqual(self._update_xccdf_file('needs_inspection', 'MEDIUM'), 1)

    def test_check_inplace_risk_slight(self):
        self.assertEqual(self._update_xccdf_file('needs_inspection', 'SLIGHT'), 1)

    def test_check_inplace_risk_extreme(self):
        self.assertEqual(self._update_xccdf_file('fail', 'EXTREME'), 2)

    def test_fail_return_value(self):
        self.assertEqual(self._update_xccdf_file('fail', None), 2)

    def test_unknown_return_values(self):
        expected_value = 'unknown'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 2)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)

    def test_pass_return_values(self):
        expected_value = 'pass'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 0)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)

    def test_fixed_return_values(self):
        expected_value = 'fixed'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 1)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)

    def test_informational_return_values(self):
        expected_value = 'informational'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 4)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)

    def test_not_applicable_return_values(self):
        expected_value = 'not_applicable'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 5)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)

    def test_error_return_values(self):
        expected_value = 'error'
        self.assertEqual(self._update_xccdf_file(expected_value, None), 3)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk), 3)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestRiskCheck))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
