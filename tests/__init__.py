from tests import test_preup
from tests import test_xml
from tests import unittest
from tests import test_oscap
from tests import test_api
from tests import test_kickstart


def suite():
    suite = unittest.TestSuite()
    suite.addTests(test_preup.suite())
    suite.addTests(test_xml.suite())
    suite.addTests(test_oscap.suite())
    suite.addTests(test_api.suite())
    suite.addTests(test_kickstart.suite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())