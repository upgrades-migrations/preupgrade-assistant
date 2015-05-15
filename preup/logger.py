
from __future__ import unicode_literals, print_function
import logging
import os
import sys
from preup import settings


# Currently we have only on log
logger = logging.getLogger('preupgrade-assistant')
try:
    hdlr = logging.FileHandler(os.path.join(settings.log_dir, "preupg.log"))
except IOError:
    # python 2.6 uses argument 'strm', where python 2.7 uses 'stream'
    # therefore don't rather specify the argument
    hdlr = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

if(sys.version_info[0] == 2):
    def log_message(message, print_output=1, new_line=True, level=logging.INFO, log=True):
        """ if verbose, log `msg % args` to stdout """
        if int(print_output) > 0:
            sys.stdout.write(message.encode(settings.defenc))
            sys.stdout.flush()
            # This is used in case that we do not want to print the new line
            if new_line:
                sys.stdout.write("\n")
                sys.stdout.flush()
        if log:
            logger.log(level, message)
else:
    def log_message(message, print_output=1, new_line=True, level=logging.INFO, log=True):
        """ if verbose, log `msg % args` to stdout """
        if int(print_output) > 0:
            endline = "\n" if newline else ""
            print(message, end=endline, file=sys.stdout, flush=True)
        if log:
            logger.log(level, message)
