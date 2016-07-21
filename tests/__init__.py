import unittest
import os


def suite():
    suite = unittest.TestSuite()
    dirname = os.path.join(os.path.dirname(__file__), 'tmp')
    solution_txt = 'solution.txt'
    os.environ['XCCDF_VALUE_TMP_PREUPGRADE'] = dirname
    os.environ['CURRENT_DIRECTORY'] = dirname
    os.environ['XCCDF_VALUE_SOLUTION_FILE'] = solution_txt
    os.environ['XCCDF_VALUE_REPORT_DIR'] = dirname
    os.environ['XCCDF_RESULT_ERROR'] = "3"
    os.environ['XCCDF_RESULT_FAILED'] = "2"
    os.environ['XCCDF_RESULT_UNKNOWN'] = "2"
    os.environ['XCCDF_RESULT_FIXED'] = "1"
    os.environ['XCCDF_RESULT_NEEDS_INSPECTION'] = "1"
    os.environ['XCCDF_RESULT_NEEDS_ACTION'] = "1"
    os.environ['XCCDF_RESULT_NOT_APPLICABLE'] = "10"
    from tests import test_preup
    from tests import test_xml
    from tests import test_generation
    from tests import test_api
    from tests import test_kickstart
    from tests import test_inplace_risks
    suite.addTests(test_preup.suite())
    suite.addTests(test_xml.suite())
    suite.addTests(test_kickstart.suite())
    suite.addTests(test_inplace_risks.suite())
    suite.addTests(test_api.suite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
