# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import optparse
from optparse import OptionValueError

from preupg import settings
from preupg.version import VERSION


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
                    raise OptionValueError("Specify at most one argument for"
                                           " upload option.")


class CLI(object):

    """Class for processing data from commandline"""

    def __init__(self, args=None):
        """parse arguments"""
        self.parser = optparse.OptionParser(
            add_help_option=False,
            version="Preupgrade Assistant %s" % VERSION
        )

        self.add_args()
        if args:
            self.opts, self.args = self.parser.parse_args(args=args)
        else:
            self.opts, self.args = self.parser.parse_args()
        
        self.resolve_option_dependencies()

    def add_args(self):
        self.parser.add_option(
            "-h", "--help",
            action="help",
            help="Show help message and exit."
        )
        self.parser.add_option(
            "-S", "--skip-common",
            action="store_true",
            help="Skip generating files containing information about the"
                 " system. For assessing the system these files are needed"
                 " (by modules) but in the case the system remains the same"
                 " (the same installed packages, configuration files not"
                 " touched, etc.) they can be reused from the previous runs of"
                 " Preupgrade Assistant."
        )
        self.parser.add_option(
            "-d", "--debug",
            action="store_true",
            help="Turn on debugging mode."
        )
        self.parser.add_option(
            "-u", "--upload",
            dest="upload",
            metavar="URL",
            action="callback",
            callback=upload_callback,
            help="Upload a system assessment result to Preupgrade Assistant"
                 " WEB-UI."
        )
        self.parser.add_option(
            "-r", "--results",
            metavar="TARBALL",
            help="Provide path to a system assessment result tarball which is"
                 " to be uploaded to WEB-UI. By default, the result tarballs"
                 " can be found in %s." % settings.assessment_results_dir
        )
        self.parser.add_option(
            "-l", "--list-contents-set",
            action="store_true",
            help="List all the available sets of modules. They are searched"
                 " for in %s." % settings.source_dir
        )
        self.parser.add_option(
            "-s", "--scan",
            metavar="MODULE_SET",
            help="Provide name of the set of modules which are to be used for"
                 " assessing the system. By default, if there is just one set"
                 " in %s, Preupgrade Assistant uses that one. Use"
                 " --list-contents-set option to get a list of possible"
                 " values." % settings.source_dir
        )
        self.parser.add_option(
            "-c", "--contents",
            metavar="ALL_XCCDF_PATH",
            help="Provide path to all-xccdf.xml of the set of modules which is"
                 " to be used for assesing the system. By default, if there is"
                 " just one set in %s, Preupgrade Assistant uses that one."
                 " Option --scan works similarly." % settings.source_dir
        )
        self.parser.add_option(
            "--riskcheck",
            action="store_true",
            default=False,
            help="Return the highest reported level of risk or result related"
                 " to system upgrade. Run Preupgrade Assistant first -"
                 " assessment of the system needs to be performed before using"
                 " this option. When this option is used in concert with"
                 " --verbose option, summary of the risks are printed to"
                 " STDOUT. If the --verbose option is used once, just HIGH and"
                 " EXTREME risks are printed. If it is used twice, all the"
                 " risks are printed. " + " " * 30 +
                 "Return codes:" + " " * 45 +
                 "0 ... SLIGHT or MEDIUM risk or needs_inspection, fixed, "
                 "informational, not_applicable, not_selected, not_checked or"
                 " pass result." + " " * 50 +
                 "1 ... HIGH risk or needs_action result." + " " * 25 +
                 "2 ... EXTREME risk or error or fail result."
        )
        self.parser.add_option(
            "--force",
            action="store_true",
            default=False,
            help="Suppress user interaction."
        )
        self.parser.add_option(
            "--text",
            action="store_true",
            default=False,
            help="Generate plain text assessment report alongside XML and HTML"
                 " reports. The text report is converted from HTML using"
                 " elinks, lynx or w3m tool."
        )
        self.parser.add_option(
            "-v", "--verbose",
            action="count",
            default=0,
            help="Show more information during the assessment."
        )
        self.parser.add_option(
            "--cleanup",
            action="store_true",
            default=False,
            help="Remove all the files created by previous runs of Preupgrade"
                 " Assistant."
        )
        self.parser.add_option(
            "-m", "--mode",
            metavar="MODE",
            choices=['migrate', 'upgrade'],
            help="Select what you plan to do with the system after performing"
                 " its assessment by Preupgrate Assistant - migration or"
                 " upgrade. Both modes are selected by default. This option"
                 " may only affect behaviour of the modules - they can provide"
                 " different results when only one mode is selected. Use one"
                 " of these values: migrate, upgrade. It may be that modules"
                 " behave the same no matter what mode is selected."
        )
        self.parser.add_option(
            "--select-rules",
            metavar="RULES",
            help="Execute just a subset of modules out of a module set."
                 " Multiple modules are to be separated by a comma."
        )
        self.parser.add_option(
            "--list-rules",
            action="store_true",
            default=False,
            help="List all the modules available within a module set."
        )
        self.parser.add_option(
            "--dst-arch",
            metavar="ARCH",
            help=(
                "Specify an architecture of the system to be migrate to."
                " Available option are: %s. Use of the option is expected on"
                " 32-bit systems as by the release of RHEL 7, 32-bit hardware"
                " support has been dropped."
                % ", ".join(settings.migration_options)
            )
        )
        self.parser.add_option(
            "--old-report-style",
            action="store_true",
            help="Generate report with simpler style than the default."
        )

    def resolve_option_dependencies(self):
        if self.opts.scan and self.opts.contents:
            raise OptionValueError("Use either --scan or --contents option,"
                                   " not both.")


if __name__ == '__main__':
    x = CLI()
    print(x.args.id)
