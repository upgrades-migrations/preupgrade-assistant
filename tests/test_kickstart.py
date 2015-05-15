
from __future__ import unicode_literals
import unittest
import os


class TestKickstart(unittest.TestCase):

    def setUp(self):
        dir_name = os.path.join(os.getcwd(), 'tests', 'FOOBAR6_7')

        pass

    def tearDown(self):
        pass


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestKickstart))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
