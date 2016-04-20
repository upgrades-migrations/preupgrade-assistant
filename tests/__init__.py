import unittest
import test_preup
import test_xml
import test_oscap
import test_generation
import test_api
import test_kickstart


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
