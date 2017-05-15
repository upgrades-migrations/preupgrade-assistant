import unittest

try:
    import base
except ImportError:
    import tests.base as base
import inspect
import os
import sys

from preupg import preupg_diff


class TestPreupgDiff(base.TestCase):

    current_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))

    class argv_mocked(list):
        pass

    class dummy_mock(base.MockFunction):
        def __call__(self, *args, **kwargs):
            pass

    class print_difference_status_mock(base.MockFunction):
        def __call__(self, num_new_xml_rules, num_diff_xml_rules):
            self.num_new_rules = num_new_xml_rules
            self.num_diff_rules = num_diff_xml_rules

    @base.mock(sys, "argv", argv_mocked)
    @base.mock(preupg_diff, "save_diff_to_xml_and_html_file", dummy_mock())
    @base.mock(preupg_diff, "print_difference_status",
               print_difference_status_mock())
    def test_xml_on_input(self):
        sys.argv = [
            "preupg-diff",
            os.path.join(self.current_dir,
                         "generated_results",
                         "inplace_combined_risk_test.xml"),
            os.path.join(self.current_dir,
                         "generated_results",
                         "inplace_risk_test.xml")]

        preupg_diff.run()

        self.assertEqual(preupg_diff.print_difference_status.num_new_rules, 2)
        self.assertEqual(preupg_diff.print_difference_status.num_diff_rules, 1)

    class stringify_children_mock(base.MockFunction):
        def __call__(self, tag_obj):
            self.children_as_str = preupg_diff.stringify_children_orig(tag_obj)
            return self.children_as_str

    @base.mock(preupg_diff, "stringify_children", stringify_children_mock())
    def test_stringify_solution_text(self):
        preupg_diff.ResultXML(os.path.join(self.current_dir,
                                           "generated_results",
                                           "inplace_risk_test.xml"))
        self.assertEqual(preupg_diff.stringify_children.children_as_str,
                         'str1<br xmlns:xhtml="http://www.w3.org/1999/xhtml/"'
                         ' xmlns:ns0="http://checklists.nist.gov/xccdf/1.2"/>'
                         'str2')


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPreupgDiff))
    return suite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=3).run(suite())
