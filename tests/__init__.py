import tests.test_preup
import tests.test_xml
import unittest
import tests.test_oscap
import tests.test_generation


def suite():
    suite = unittest.TestSuite()
    suite.addTests(test_preup.suite())
    suite.addTests(test_xml.suite())
    suite.addTests(test_oscap.suite())
    #suite.addTests(test_generation.suite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
