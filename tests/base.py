import unittest

"""
Use this module to subclass and enhance upstream classes
with test-suite-specific features like custom asserts
for unittest.TestCase.
"""


class TestCase(unittest.TestCase):

    # ported from 2.7's unittest
    def assertIsNone(self, obj, msg=None):
        """Same as self.assertTrue(obj is None), with a nicer
        default message."""
        if obj is not None:
            standardMsg = '%r is not None' % obj
            self.fail(self._formatMessage(msg, standardMsg))

    # ported from 2.7's unittest
    def assertIsNotNone(self, obj, msg=None):
        """Included for symmetry with assertIsNone."""
        if obj is None:
            standardMsg = 'unexpectedly None'
            self.fail(self._formatMessage(msg, standardMsg))
