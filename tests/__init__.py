import unittest
import os

from preupg import settings

dirname = os.path.join(os.path.dirname(__file__), 'tmp')
solution_txt = settings.solution_txt
os.environ['XCCDF_VALUE_TMP_PREUPGRADE'] = dirname
os.environ['CURRENT_DIRECTORY'] = dirname
os.environ['XCCDF_VALUE_REPORT_DIR'] = dirname
os.environ['XCCDF_VALUE_CURRENT_DIRECTORY'] = os.path.join(os.path.dirname(__file__), "..")
os.environ['XCCDF_RESULT_ERROR'] = "3"
os.environ['XCCDF_RESULT_FAILED'] = "2"
os.environ['XCCDF_RESULT_FAIL'] = "2"
os.environ['XCCDF_RESULT_FIXED'] = "1"
os.environ['XCCDF_RESULT_NEEDS_INSPECTION'] = "1"
os.environ['XCCDF_RESULT_NEEDS_ACTION'] = "1"
os.environ['XCCDF_RESULT_NOT_APPLICABLE'] = "10"
os.environ['XCCDF_VALUE_MODULE_PATH'] = "test_script_api"


def suite():
    settings.log_dir = os.getcwd()
    settings.preupg_log = os.path.join(settings.log_dir, "preupg.log")
    settings.preupg_report_log = os.path.join(settings.log_dir, "preupg-report.log")

    suite = unittest.TestSuite()
    from tests import test_preupg
    from tests import test_xml
    from tests import test_generation
    from tests import test_api
    from tests import test_kickstart
    from tests import test_inplace_risks
    from tests import test_creator
    from tests import test_preupg_diff
    suite.addTests(test_preupg.suite())
    suite.addTests(test_xml.suite())
    suite.addTests(test_generation.suite())
    suite.addTests(test_api.suite())
    suite.addTests(test_kickstart.suite())
    suite.addTests(test_inplace_risks.suite())
    suite.addTests(test_creator.suite())
    suite.addTests(test_preupg_diff.suite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
