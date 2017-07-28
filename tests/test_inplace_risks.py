from __future__ import unicode_literals
import unittest
import tempfile
import shutil
import os

from preupg.xccdf import XccdfHelper
from preupg.utils import FileHelper
from preupg.report_parser import ReportParser
from preupg.settings import ResultBasedReturnCodes

try:
    import base
except ImportError:
    import tests.base as base


def _update_xccdf_file(class_id, result_value, risk):
    temp_file = class_id._copy_xccdf_file(result_value, risk)
    ReportParser(temp_file).replace_inplace_risk()
    return_code = XccdfHelper.check_inplace_risk(temp_file, 0)
    shutil.rmtree(os.path.dirname(temp_file))
    return return_code


class TestRiskCheck(base.TestCase):

    risks = ['SLIGHT', 'MEDIUM', 'HIGH', 'EXTREME']

    @staticmethod
    def _copy_xccdf_file(update_return_value=None, update_text=None):
        temp_dir = tempfile.mkdtemp()
        xccdf_file = os.path.join(os.getcwd(), 'tests', 'generated_results',
                                  'inplace_risk_test.xml')
        temp_file = os.path.join(temp_dir, 'inplace_risk_test_updated.xml')
        shutil.copyfile(xccdf_file, temp_file)
        content = FileHelper.get_file_content(temp_file, 'rb',
                                              decode_flag=False)
        content = content.replace(b'RESULT_VALUE1', update_return_value)
        new_text = b'preupg.risk.%s: Test %s Inplace risk' % (update_text,
                                                              update_text)
        if update_text is not None:
            content = content.replace(b'INPLACE_TAG1', new_text)
        else:
            content = content.replace(b'INPLACE_TAG1', "")
        FileHelper.write_to_file(temp_file, 'wb', content)
        return temp_file

    def test_check_inplace_risk_high(self):
        self.assertEqual(_update_xccdf_file(TestRiskCheck, 'fail', 'HIGH'),
                         ResultBasedReturnCodes.NEEDS_ACTION)

    def test_check_inplace_risk_medium(self):
        self.assertEqual(_update_xccdf_file(TestRiskCheck, 'fail', 'MEDIUM'),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_check_inplace_risk_slight(self):
        self.assertEqual(_update_xccdf_file(TestRiskCheck, 'fail', 'SLIGHT'),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_check_inplace_risk_extreme(self):
        self.assertEqual(_update_xccdf_file(TestRiskCheck, 'fail', 'EXTREME'),
                         ResultBasedReturnCodes.FAIL)

    def test_fail_return_value(self):
        self.assertEqual(_update_xccdf_file(TestRiskCheck, 'fail', None),
                         ResultBasedReturnCodes.ERROR)

    def test_pass_return_values(self):
        expected_value = 'pass'
        self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                            expected_value, None),
                         ResultBasedReturnCodes.PASS)
        for risk in self.risks:
            self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                                expected_value, risk),
                             ResultBasedReturnCodes.ERROR)

    def test_fixed_return_values(self):
        expected_value = 'fixed'
        self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                            expected_value, None),
                         ResultBasedReturnCodes.FIXED)
        for risk in self.risks:
            self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                                expected_value, risk),
                             ResultBasedReturnCodes.ERROR)

    def test_informational_return_values(self):
        expected_value = 'informational'
        self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                            expected_value, None),
                         ResultBasedReturnCodes.INFORMATIONAL)
        for risk in self.risks:
            self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                                expected_value, risk),
                             ResultBasedReturnCodes.ERROR)

    def test_not_applicable_return_values(self):
        expected_value = 'notapplicable'
        self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                            expected_value, None),
                         ResultBasedReturnCodes.NOT_ALL)
        for risk in self.risks:
            self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                                expected_value, risk),
                             ResultBasedReturnCodes.ERROR)

    def test_error_return_values(self):
        expected_value = 'error'
        self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                            expected_value, None),
                         ResultBasedReturnCodes.ERROR)
        for risk in self.risks:
            self.assertEqual(_update_xccdf_file(TestRiskCheck,
                                                expected_value, risk),
                             ResultBasedReturnCodes.ERROR)


class TestCombinedRiskCheck(base.TestCase):

    @staticmethod
    def _copy_xccdf_file(update_return_values=None, update_text=None):
        temp_dir = tempfile.mkdtemp()
        xccdf_file = os.path.join(os.getcwd(), 'tests', 'generated_results',
                                  'inplace_combined_risk_test.xml')
        temp_file = os.path.join(temp_dir, 'all-xccdf.xml')
        shutil.copyfile(xccdf_file, temp_file)
        content = FileHelper.get_file_content(temp_file, 'rb',
                                              decode_flag=False)
        if update_text:
            if update_text[0] is not None:
                new_text = b'preupg.risk.%s: Test %s Inplace risk' % (
                    update_text[0], update_text[0])
                if update_text is not None:
                    content = content.replace(b'INPLACE_TAG1', new_text)
                else:
                    content = content.replace(b'INPLACE_TAG1', "")
            if update_text[1] is not None:
                new_text = b'preupg.risk.%s: Test %s Inplace risk' % (
                    update_text[1], update_text[1])
                if update_text is not None:
                    content = content.replace(b'INPLACE_TAG2', new_text)
                else:
                    content = content.replace(b'INPLACE_TAG2', "")
        content = content.replace(b'RESULT_VALUE1', update_return_values[0])
        content = content.replace(b'RESULT_VALUE2', update_return_values[1])
        FileHelper.write_to_file(temp_file, 'wb', content)
        return temp_file

    def test_error_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['error', 'pass'],
                                            [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_error_failed(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['error', 'fail'],
                                            [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_error_informational(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['error', 'informational'],
                                            [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_needs_inspection_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['needs_inspection', 'pass'],
                                            [None, None]),
                         ResultBasedReturnCodes.NEEDS_INSPECTION)

    def test_informational_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['informational', 'pass'],
                                            [None, None]),
                         ResultBasedReturnCodes.INFORMATIONAL)

    def test_fixed_informational(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['fixed', 'informational'],
                                            [None, None]),
                         ResultBasedReturnCodes.FIXED)

    def test_fixed_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['fixed', 'pass'],
                                            [None, None]),
                         ResultBasedReturnCodes.FIXED)

    def test_pass_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['pass', 'pass'],
                                            [None, None]),
                         ResultBasedReturnCodes.PASS)

    def test_needs_action_failed(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['needs_action', 'fail'],
                                            ['HIGH', 'EXTREME']),
                         ResultBasedReturnCodes.FAIL)

    def test_fixed_failed(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['fixed', 'fail'],
                                            [None, 'EXTREME']),
                         ResultBasedReturnCodes.FAIL)

    def test_fixed_failed_none(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['fixed', 'fail'],
                                            [None, None]),
                         ResultBasedReturnCodes.ERROR)

    def test_fixed_information_risk(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['fixed', 'informational'],
                                            [None, 'HIGH']),
                         ResultBasedReturnCodes.ERROR)

    def test_not_applicable_pass(self):
        self.assertEqual(_update_xccdf_file(TestCombinedRiskCheck,
                                            ['notapplicable', 'pass'],
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
