from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preupg.xccdf import XccdfHelper
from preupg.utils import FileHelper
from preupg import settings
from preupg.settings import ResultBasedReturnCodes

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
        self.assertEqual(self._update_xccdf_file('needs_action', 'HIGH'),
                         ResultBasedReturnCodes.NEEDS_ACTION)

    def test_check_inplace_risk_medium(self):
        self.assertEqual(self._update_xccdf_file('needs_inspection', 'MEDIUM'),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_check_inplace_risk_slight(self):
        self.assertEqual(self._update_xccdf_file('needs_inspection', 'SLIGHT'),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_check_inplace_risk_extreme(self):
        self.assertEqual(self._update_xccdf_file('fail', 'EXTREME'),
                         ResultBasedReturnCodes.FAIL)

    def test_fail_return_value(self):
        self.assertEqual(self._update_xccdf_file('fail', None),
                         ResultBasedReturnCodes.FAIL)

    def test_pass_return_values(self):
        expected_value = 'pass'
        self.assertEqual(self._update_xccdf_file(expected_value, None),
                         ResultBasedReturnCodes.PASS)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk),
                             ResultBasedReturnCodes.PASS)

    def test_fixed_return_values(self):
        expected_value = 'fixed'
        self.assertEqual(self._update_xccdf_file(expected_value, None),
                         ResultBasedReturnCodes.FIXED)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk),
                             ResultBasedReturnCodes.FIXED)

    def test_informational_return_values(self):
        expected_value = 'informational'
        self.assertEqual(self._update_xccdf_file(expected_value, None),
                         ResultBasedReturnCodes.INFORMATIONAL)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk),
                             ResultBasedReturnCodes.INFORMATIONAL)

    def test_not_applicable_return_values(self):
        expected_value = 'not_applicable'
        self.assertEqual(self._update_xccdf_file(expected_value, None),
                         ResultBasedReturnCodes.NOT_ALL)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk),
                             ResultBasedReturnCodes.NOT_ALL)

    def test_error_return_values(self):
        expected_value = 'error'
        self.assertEqual(self._update_xccdf_file(expected_value, None),
                         ResultBasedReturnCodes.ERROR)
        for risk in self.risks:
            self.assertEqual(self._update_xccdf_file(expected_value, risk),
                             ResultBasedReturnCodes.ERROR)


class TestCombinedRiskCheck(base.TestCase):

    risks = ['SLIGHT', 'MEDIUM', 'HIGH', 'EXTREME']

    def _copy_xccdf_file(self, update_text=None, update_return_values=None):
        temp_dir = tempfile.mkdtemp()
        xccdf_file = os.path.join(os.getcwd(), 'tests', 'generated_results', 'inplace_combined_risk_test.xml')
        temp_file = os.path.join(temp_dir, 'all-xccdf.xml')
        shutil.copyfile(xccdf_file, temp_file)
        content = FileHelper.get_file_content(temp_file, 'rb', decode_flag=False)
        if update_text:
            if update_text[0] is not None:
                new_text = b'preupg.risk.%s: Test %s Inplace risk' % (update_text[0], update_text[0])
                if update_text is not None:
                    content = content.replace(b'INPLACE_TAG1', new_text)
                else:
                    content = content.replace(b'INPLACE_TAG1', "")
            if update_text[1] is not None:
                new_text = b'preupg.risk.%s: Test %s Inplace risk' % (update_text[1], update_text[1])
                if update_text is not None:
                    content = content.replace(b'INPLACE_TAG2', new_text)
                else:
                    content = content.replace(b'INPLACE_TAG2', "")
        content = content.replace(b'RESULT_VALUE1', update_return_values[0])
        content = content.replace(b'RESULT_VALUE2', update_return_values[1])
        FileHelper.write_to_file(temp_file, 'wb', content)
        return temp_file

    def _update_xccdf_file(self, return_value, risk):
        temp_file = self._copy_xccdf_file(update_return_values=return_value,
                                          update_text=risk)
        return_value = XccdfHelper.check_inplace_risk(os.path.join(os.path.dirname(temp_file), 'all-xccdf.xml'), 0)
        shutil.rmtree(os.path.dirname(temp_file))
        return return_value

    def test_error_pass(self):
        self.assertEqual(self._update_xccdf_file(['error', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_error_failed(self):
        self.assertEqual(self._update_xccdf_file(['error', 'fail'],
                                                 [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_error_informational(self):
        self.assertEqual(self._update_xccdf_file(['error', 'informational'],
                                                 [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_needs_inspection_pass(self):
        self.assertEqual(self._update_xccdf_file(['needs_inspection', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_informational_pass(self):
        self.assertEqual(self._update_xccdf_file(['informational', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.INFORMATIONAL)

    def test_fixed_informational(self):
        self.assertEqual(self._update_xccdf_file(['fixed', 'informational'],
                                                 [None, None]),
                         ResultBasedReturnCodes.FIXED)

    def test_fixed_pass(self):
        self.assertEqual(self._update_xccdf_file(['fixed', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.FIXED)

    def test_pass_pass(self):
        self.assertEqual(self._update_xccdf_file(['pass', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.PASS)

    def test_needs_action_failed(self):
        self.assertEqual(self._update_xccdf_file(['needs_action', 'fail'],
                                                 ['HIGH', 'EXTREME']),
                         ResultBasedReturnCodes.FAIL)

    def test_fixed_failed(self):
        self.assertEqual(self._update_xccdf_file(['fixed', 'fail'],
                                                 [None, 'EXTREME']),
                         ResultBasedReturnCodes.FAIL)

    def test_fixed_failed_none(self):
        self.assertEqual(self._update_xccdf_file(['fixed', 'fail'],
                                                 [None, None]),
                         ResultBasedReturnCodes.FAIL)

    def test_fixed_information_risk(self):
        self.assertEqual(self._update_xccdf_file(['fixed', 'informational'],
                                                 [None, 'HIGH']),
                         ResultBasedReturnCodes.FIXED)

    def test_not_applicable_pass(self):
        self.assertEqual(self._update_xccdf_file(['not_applicable', 'pass'],
                                                 [None, None]),
                         ResultBasedReturnCodes.NOT_ALL)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestRiskCheck))
    suite.addTest(loader.loadTestsFromTestCase(TestCombinedRiskCheck))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
