# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
#import argparse
import optparse
from optparse import OptionValueError

from preup.constants import *


class CLICreator(object):

    """Class for processing data from commandline"""

    def __init__(self, args=None):
        """parse arguments"""
        self.parser = optparse.OptionParser(usage=USAGE, description=PROGRAM_DESCRIPTION)

        #self.parser.usage = "%%prog [-v] <content_file>"

        self.add_args()
        if args:
            self.opts, self.args = self.parser.parse_args(args=args)
        else:
            self.opts, self.args = self.parser.parse_args()

    def add_args(self):
        self.parser.add_option(
            "-m",
            "--main-directory",
            dest="maindir",
            help="Specify main directory for content",
        )
        self.parser.add_option(
            "-v",
            "--validate",
            action='store_true',
            help="Validate content(s)"
        )
        self.parser.add_option(
            "-d",
            "--debug",
            action='store_true',
            help="Turn on debugging mode"
        )

if __name__ == '__main__':
    x = CLICreator()

