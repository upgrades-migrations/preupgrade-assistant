import test_preup
import test_xml
import unittest
import test_oscap


def suite():
    suite = unittest.TestSuite()
    suite.addTests(test_preup.suite())
    suite.addTests(test_xml.suite())
    suite.addTests(test_oscap.suite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())