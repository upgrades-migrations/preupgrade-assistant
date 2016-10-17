# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
#import argparse
import optparse
from optparse import OptionValueError

from preup.constants import *


def upload_callback(option, dummy_opt_str, dummy_value, parser):
    if len(parser.rargs) == 0:
        setattr(parser.values, option.dest, True)
    else:
        if parser.rargs[0].startswith('-'):
            setattr(parser.values, option.dest, True)
        else:
            setattr(parser.values, option.dest, parser.rargs[0])
            try:
                second_arg = parser.rargs[1]
            except IndexError:
                pass
            else:
                if not second_arg.startswith('-'):
                    raise OptionValueError("Specify at most one argument for upload option.")


def optional_rh_arg(arg_default):
    def func(option, opt_str, value, parser):
        if parser.rargs and not parser.rargs[0].startswith('-'):
            val = parser.rargs[0]
            parser.rargs.pop(0)
        else:
            val = arg_default
        setattr(parser.values, option.dest, val)
    return func


class CLI(object):

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
            "--skip-common",
            action="store_true",
            help="Skip generation of common files"
        )
        self.parser.add_option(
            "-d", "--debug",
            action="store_true",
            help="Turn on debugging mode"
        )
        self.parser.add_option(
            "-u", "--upload",
            dest="upload",
            action="callback",
            callback=upload_callback,
            help="--upload http://example.com:8099/submit/\n\n\n\n\n\n\n\n\n\n\n\n\n\
Upload results to preupgrade assistant WEB-UI"
        )
        self.parser.add_option(
            "-r", "--results",
            type=str,
            metavar="results.tar.gz",
            help="Path to tarball with results when uploading to WEB-UI"
        )
        self.parser.add_option(
            "-l",
            "--list-contents-set",
            action="store_true",
            help="List upgrade path"
        )
        self.parser.add_option(
            "-s",
            "--scan",
            metavar="PATH",
            help="Assess source system"
        )
        self.parser.add_option(
            "-c",
            "--contents",
            help="Path to contents set"
        )
        self.parser.add_option(
            "--riskcheck",
            action="store_true",
            default=False,
            help="Checks preupgrade assessment for INPLACE RISKS." + "\n"*15 +
                 "Return values:" + "\n"*45 +
                 "0 ... SLIGHT risk was detected." + "\n" * 25 +
                 "1 ... MEDIUM, HIGH risks were detected." + "\n" * 20 +
                 "2 ... EXTREME risk was detected."
        )
        self.parser.add_option(
            "--force",
            action="store_true",
            default=False,
            help="Suppress user interaction"
        )
        self.parser.add_option(
            "--text",
            action="store_true",
            default=False,
            help="Convert HTML results to text form by elinks, lynx or w3m"
        )
        self.parser.add_option(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Verbose mode"
        )
        self.parser.add_option(
            "--cleanup",
            action="store_true",
            default=False,
            help="Clean data created by preupgrade-assistant"
        )
        self.parser.add_option(
            "-m",
            "--mode",
            metavar="MODE",
            choices=['migrate', 'upgrade'],
            help="Select mode which can be used for migration or upgrade"
        )
        self.parser.add_option(
            "--kickstart",
            action="store_true",
            default=False,
            help="Generate kickstart"
        )
        self.parser.add_option(
            "--select-rules",
            metavar="RULES",
            help="Run a set of contents give as a comma-separated list."
        )
        self.parser.add_option(
            "--list-rules",
            action="store_true",
            default=False,
            help="List available contents"
        )
        self.parser.add_option(
            "--version",
            action="store_true",
            default=False,
            help="Show Preupgrade Assistant version"
        )
        self.parser.add_option(
            "--dst-arch",
            metavar="DSTARCH",
            help="""
                 Specify target/destination architecture where you want to migrate
                 (e.g.: x86_64). Use of the option is expected on 32b systems.
                 """
        )


if __name__ == '__main__':
    x = CLI()
    print(x.args.id)
