import abc
from functools import wraps
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


def mock(class_or_module, orig_obj, mock_obj):
    """This is a decorator to be applied to any test method that needs to mock
    some module/class object (be it function, method or variable). It replaces
    the original object with any arbitrary object. The original is still
    accessible through "<original object name>_orig" attribute.

    Parameters:
    class_or_module - module/class in which the original function/method is
                      defined
    orig_obj - name of the original object as a string
    mock_obj - object that will replace the orig_obj, for example:
               -- instance of some fake function
               -- string

    Example:
    @tests.mock(utils, "run_subprocess", run_subprocess_mocked())
    -- replaces the original run_subprocess function from the utils module
       with the run_subprocess_mocked function.
    @tests.mock(logging.FileHandler, "_open", FileHandler_open_mocked())
    -- replaces the original _open method of the FileHandler class within
       the logging module with the FileHandler_open_mocked function.
    @tests.mock(gpgkey, "gpg_key_system_dir", "/nonexisting_dir/")
    -- replaces the gpgkey module-scoped variable gpg_key_system_dir with the
       "/nonexisting_dir/" string
    """
    def wrap(fn):
        # The @wraps decorator below makes sure the original object name
        # and docstring (in case of a method/function) are preserved.
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            # Save temporarily the original object
            orig_obj_saved = getattr(class_or_module, orig_obj)
            # Replace the original object with the mocked one
            setattr(class_or_module, orig_obj, mock_obj)
            # To be able to use the original object within the mocked object
            # (e.g. to have the mocked function just as a wrapper for the
            # original function), save it as a temporary attribute
            # named "<original object name>_orig"
            orig_obj_attr = "{0}_orig".format(orig_obj)
            setattr(class_or_module, orig_obj_attr, orig_obj_saved)
            # Call the decorated test function
            return_value = fn(*args, **kwargs)
            # Restore the original object
            setattr(class_or_module, orig_obj, orig_obj_saved)
            # Remove the temporary attribute holding the original object
            delattr(class_or_module, orig_obj_attr)
            return return_value
        return wrapped_fn
    return wrap


class MockFunction(object):
    """This class should be used as a base class when creating a mocked
    function.

    Example:
    from convert2rhel import tests  # Imports tests/__init__.py
    class run_subprocess_mocked(tests.MockFunction):
        ...
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self):
        """To be implemented when inheriting this class. The input parameters
        should either mimic the parameters of the original function/method OR
        use generic input parameters (*args, **kwargs).

        Examples:
        def __call__(self, cmd, print_output=True, shell=False):
            # ret_val to be set within the test or within __init__ first
            return self.ret_val

        def __call__(self, *args, **kwargs):
            pass
        """
