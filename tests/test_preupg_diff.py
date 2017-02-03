import unittest

try:
    import base
except ImportError:
    import tests.base as base
import sys

from preupg import preupg_diff


class TestPreupgDiff(base.TestCase):

    class dummy_mock(base.MockFunction):
        def __call__(self, *args, **kwargs):
            pass

    class print_difference_status_mock(base.MockFunction):
        def __call__(self, num_new_xml_rules, num_diff_xml_rules):
            self.num_new_rules = num_new_xml_rules
            self.num_diff_rules = num_diff_xml_rules

    @base.mock(sys, "argv", [
        'preupg-diff',
        'tests/generated_results/inplace_combined_risk_test.xml',
        'tests/generated_results/inplace_risk_test.xml'])
    @base.mock(preupg_diff, "save_diff_to_xml_and_html_file", dummy_mock())
    @base.mock(preupg_diff, "print_difference_status",
               print_difference_status_mock())
    def test_xml_on_input(self):
        preupg_diff.run()

        self.assertEqual(preupg_diff.print_difference_status.num_new_rules, 2)
        self.assertEqual(preupg_diff.print_difference_status.num_diff_rules, 1)

    @base.mock(sys, "argv", [
        'preupg-diff',
        'tests/generated_results/',
        'tests/generated_results/inplace_risk_test.xml'])
    @base.mock(preupg_diff, "save_diff_to_xml_and_html_file", dummy_mock())
    @base.mock(preupg_diff, "print_difference_status",
               print_difference_status_mock())
    def test_dir_on_input(self):
        preupg_diff.run()

        self.assertEqual(preupg_diff.print_difference_status.num_new_rules, 2)
        self.assertEqual(preupg_diff.print_difference_status.num_diff_rules, 0)


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPreupgDiff))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
