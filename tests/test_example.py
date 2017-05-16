# CONVENTION FOR WRITING UNIT TESTS
#  - The python file with unit tests shall be named with 'test_' prefix.
#  - Test methods need to be defined within a class derived from base.TestCase
#    (name of the class can be arbitrary).
#  - Test methods need to be named with 'test_' prefix.
#  - A unit test shall not modify/create/remove any file during its exectution.
#  - No unit test shall rely on any other unit test, i.e. each test shall be
#    possible to execute on its own.
#  - Prefer 'mock' decorator to setUp method. Use setUp only to avoid using
#    the same mock decorator for many unit test methods. See base.py for details
#    on the usage of mock.
#  - Each python file needs to have 'suite' function defined in order to be
#    executed along the other tests using 'python setup.py test'

# TEST EXECUTION
#  - Before publishing any new or updated test, make sure it's possible to
#    execute it on its own. Run:
#       nosetests <dir_to_python_modules>.<python_module>:<class>.<method>
#  - Example:
#       nosetests tests.test_example:TestExample.test_basic_example

# STANDARD OUTPUT OF A TEST
#  - To let the tests print to stdout, use nosetests option --nocapture

# Required import
try:
    import base
except ImportError:
    import tests.base as base

# Modules/symbols to be tested or mocked
import sys
from tests import test_preupg


class TestExample(base.TestCase):

    class list_mocked(list):
        pass

    class function_mocked(base.MockFunction):
        def __call__(self):
            self.var = sys.argv[0]

    @base.mock(sys, "argv", list_mocked)
    @base.mock(test_preupg, "suite", function_mocked())
    def test_basic_example(self):
        # Do some preparation before the test
        sys.argv = ["executable"]
        # Run the method/function to be tested
        test_preupg.suite()
        # Verify the results
        self.assertEqual(test_preupg.suite.var, "executable")
