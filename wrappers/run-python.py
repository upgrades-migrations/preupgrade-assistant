#!/usr/bin/python2 -tt
# -*- coding: utf-8 -*-

import os
import sys
import optparse
import imp

from preup.utils import FileHelper, ProcessHelper
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class CheckTestScript(object):

    def __init__(self, script_name, config_file=None):
        self.script_name = script_name
        self.config_file = config_file
        self.bash_environment = []
        if config_file:
            self._load_config_file()

    def _load_config_file(self):
        config = configparser.RawConfigParser(allow_no_value=True)
        config.read(self.config_file)
        section = "preupgrade-assistant"
        if config.has_section(section):
            options = config.options(section)
            for opt in options:
                value = config.get(section, opt)
                os.environ[opt.upper()] = value
                bash_script = opt.upper() + '=' + value
                self.bash_environment.append(bash_script)

    def test_script(self):
        script_type = FileHelper.get_script_type(self.script_name)
        if script_type == "python":
            test_file = imp.load_source(os.path.basename(self.script_name)[:-3], self.script_name)
            test_file.main()
        else:
            ProcessHelper.run_subprocess(self.script_name, print_output=True)


def main():
    parser = optparse.OptionParser(usage="%prog [options] check_script",
                                   description="Test check scripts used by OpenSCAP"
                                   )
    parser.add_option('-c', '--config-file',
                      help='Config file with XCCDF predefined values.'
                      )
    opts, args = parser.parse_args()
    if len(args) == 0:
        print('Specify at least one script for testing.')
        parser.print_help()
        sys.exit(1)
    if len(args) > 1:
        print('You can test only one script at time.')
        sys.exit(1)

    cur_dir = os.path.abspath(os.path.curdir)
    config_file = None
    if opts.config_file:
        config_file = os.path.join(cur_dir, opts.config_file)
        if not os.path.exists(config_file):
            print("The '%s' config file does not exist." % config_file)
            sys.exit(1)
    full_path_script = os.path.join(cur_dir, args[0])
    if not os.path.exists(full_path_script):
        print("The script '%s' does not exist." % full_path_script)
        sys.exit(1)
    if FileHelper.check_executable(full_path_script):
        print("The script '%s' is not executable" % full_path_script)
        sys.exit(1)
    cts = CheckTestScript(full_path_script, config_file=config_file)
    cts.test_script()

if __name__ == "__main__":
    main()
