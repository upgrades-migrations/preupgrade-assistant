import sys
from os.path import dirname, realpath, join

LIB_PATH = join(dirname(realpath(__file__)), "lib")

# add LIB_PATH to PYTHON_PATH
if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)
