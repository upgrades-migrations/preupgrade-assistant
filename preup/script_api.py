# -*- coding: utf-8 -*-
"""
python API for content writers

USAGE
*****

Best way is to import all functions from this module:

from script_api import *

First thing to do is to set component:

set_component('httpd')

This is used when logging.

These functions are available:

* logging functions -- log_*
 * log message to stdout
* logging risk functions -- log_*_risk
 * log risk level -- so administrator know how risky is to inplace upgrade
* get_dest_dir -- get dir for storing configuration files
* set_component -- set component's name (for logging purposes)
* exit_* -- terminate execution with appropriate exit code
"""

from __future__ import unicode_literals, print_function
import os
import sys
import re
import shutil
from preup import utils, settings
from preup.utils import get_file_content, write_to_file

__all__ = (
    'log_debug',
    'log_info',
    'log_warning',
    'log_error',

    'log_extreme_risk',
    'log_high_risk',
    'log_medium_risk',
    'log_slight_risk',

    'get_dest_dir',
    'set_component',

    'exit_error',
    'exit_fail',
    'exit_failed',
    'exit_fixed',
    'exit_informational',
    'exit_not_applicable',
    'exit_informational',
    'exit_pass',
    'exit_unknown',
    'check_rpm_to',
    'check_applies_to',
    'solution_file',
    'switch_to_content',
    'service_is_enabled',

    'PREUPGRADE_CACHE',
    'VALUE_RPM_QA',
    'VALUE_ALLCHANGED',
    'VALUE_CONFIGCHANGED',
    'VALUE_PASSWD',
    'VALUE_CHKCONFIG',
    'VALUE_GROUP',
    'VALUE_RPMTRACKEDFILES',
    'VALUE_ALLMYFILES',
    'VALUE_EXECUTABLES',
    'VALUE_RPM_RHSIGNED',
    'VALUE_TMP_PREUPGRADE',
    'SOLUTION_FILE',
    'POSTUPGRADE_DIR',
    'KICKSTART_README',
    'MIGRATE',
    'UPGRADE',
)

CACHE = "/var/cache/preupgrade"
PREUPGRADE_CACHE = os.path.join(CACHE, "common")
VALUE_RPM_QA = os.path.join(PREUPGRADE_CACHE, "rpm_qa.log")
VALUE_ALLCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_Va.log")
VALUE_CONFIGCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_etc_Va.log")
VALUE_PASSWD = os.path.join(PREUPGRADE_CACHE, "passwd.log")
VALUE_CHKCONFIG = os.path.join(PREUPGRADE_CACHE, "chkconfig.log")
VALUE_GROUP = os.path.join(PREUPGRADE_CACHE, "group.log")
VALUE_RPMTRACKEDFILES = os.path.join(PREUPGRADE_CACHE, "rpmtrackedfiles.log")
VALUE_ALLMYFILES = os.path.join(PREUPGRADE_CACHE, "allmyfiles.log")
VALUE_EXECUTABLES = os.path.join(PREUPGRADE_CACHE, "executable.log")
VALUE_RPM_RHSIGNED = os.path.join(PREUPGRADE_CACHE, "rpm_rhsigned.log")
VALUE_TMP_PREUPGRADE = os.environ['XCCDF_VALUE_TMP_PREUPGRADE']
SOLUTION_FILE = os.environ['XCCDF_VALUE_SOLUTION_FILE']
try:
    MIGRATE = os.environ['XCCDF_VALUE_MIGRATE']
    UPGRADE = os.environ['XCCDF_VALUE_UPGRADE']
except KeyError:
    MIGRATE = 1
    UPGRADE = 1
POSTUPGRADE_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "postupgrade.d")
KICKSTART_README = os.path.join(VALUE_TMP_PREUPGRADE, "kickstart", "README")


component = "unknown"


################
# RISK LOGGING #
################

def log_risk(severity, message):
    """
    log risk level to stderr
    """
    print("INPLACERISK: %s: %s\n" % (severity, message.encode(settings.defenc)), end="", file=sys.stderr)


def log_extreme_risk(message):
    """
    log_extreme_risk(message)

    Inplace upgrade is impossible.
    """
    log_risk("EXTREME", message)


def log_high_risk(message):
    """
    log_high_risk(message)

    Administrator has to inspect and correct upgraded system so
    inplace upgrade can be used.
    """
    log_risk("HIGH", message)


def log_medium_risk(message):
    """
    log_medium_risk(message)

    inplace upgrade is possible; system after upgrade may be unstable
    """
    log_risk("MEDIUM", message)


def log_slight_risk(message):
    """
    log_slight_risk(message)

    no issues found; although there are some unexplored areas
    """
    log_risk("SLIGHT", message)


##################
# STDOUT LOGGING #
##################

def log(severity, message, component_arg=None):
    """log message to stdout"""
    global component
    comp_show = component_arg or component
    print("%s %s: %s\n" % (severity, comp_show, message.encode(settings.defenc)), end="", file=sys.stdout)


def log_error(message, component_arg=None):
    """
    log_error(message, component=None) -> None

    log message to stdout with severity error
    if you would like to change component temporary, you may pass it as argument

    use this severity if your script found something severe
    which may cause malfunction on new system
    """
    log('ERROR', message, component_arg)


def log_warning(message, component_arg=None):
    """
    log_warning(message, component_arg=None) -> None

    log message to stdout with severity warning
    if you would like to change component temporary, you may pass it as argument

    important finding, administrator of system should be aware of this
    """
    log('WARNING', message, component_arg)


def log_info(message, component_arg=None):
    """
    log_info(message, component_arg=None) -> None

    log message to stdout with severity info
    if you would like to change component temporary, you may pass it as argument

    informational message
    """
    log('INFO', message, component_arg)


def log_debug(message, component_arg=None):
    """
    log_debug(message, component_arg=None) -> None

    log message to stdout with severity debug
    if you would like to change component temporary, you may pass it as argument

    verbose information, may help with script debugging
    """
    log('DEBUG', message, component_arg)


#########
# UTILS #
#########

def get_dest_dir():
    """
    get_dest_dir()

    return absolute path to directory, where you should store files
    """
    return os.environ['XCCDF_VALUE_TMP_PREUPGRADE']


def shorten_envs():
    """make all the oscap's environemt variables shorter"""
    envs = os.environ
    prefixes = ('XCCDF_VALUE_', 'XCCDF_RESULT_')
    for env_key, env_value in envs.items():
        for prefix in prefixes:
            if env_key.startswith(prefix):
                os.environ[env_key.replace(prefix, '')] = env_value


def set_component(c):
    """configure name of component globally (it will be used in logging)"""
    global component
    component = c


# These are shortcut functions for:
#   sys.exit(int(os.environ['FAIL']))

def exit_fail():
    """
    The test failed.
    Moving to new release with this configuration will result in malfunction.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_FAIL']))


def exit_failed():
    """
    The test failed.

    Moving to new release with this configuration will result in malfunction.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_FAIL']))


def exit_error():
    """
    An error occurred and test could not complete.

    (script failed while doing its job)
    """
    sys.exit(int(os.environ['XCCDF_RESULT_ERROR']))


def exit_pass():
    """Test passed."""
    sys.exit(int(os.environ['XCCDF_RESULT_PASS']))


def exit_unknown():
    """Could not tell what happened."""
    sys.exit(int(os.environ['XCCDF_RESULT_UNKNOWN']))


def exit_not_applicable():
    """Rule did not apply to test target. (e.g. package is not installed)"""
    sys.exit(int(os.environ['XCCDF_RESULT_NOT_APPLICABLE']))


def exit_fixed():
    """Rule failed, but was later fixed."""
    sys.exit(int(os.environ['XCCDF_RESULT_FIXED']))


def exit_informational():
    """Rule failed, but was later fixed."""
    sys.exit(int(os.environ['XCCDF_RESULT_INFORMATIONAL']))


def switch_to_content():
    """Function for switch to the content directory"""
    os.chdir(os.environ['CURRENT_DIRECTORY'])


def check_applies_to(check_applies=""):
    not_applicable = 0
    if check_applies != "":
        rpms = check_applies.split(',')
        lines = get_file_content(VALUE_RPM_QA, "rb", True)
        for rpm in rpms:
            lst = filter(lambda x: rpm == x.split('\t')[0], lines)
            if not lst:
                log_info("Package %s is not installed" % rpm)
                not_applicable = 1
    if not_applicable:
        exit_not_applicable()


def check_rpm_to(check_rpm="", check_bin=""):
    not_applicable = 0

    if check_rpm != "":
        rpms = check_rpm.split(',')
        lines = get_file_content(VALUE_RPM_QA, "rb", True)
        for rpm in rpms:
            lst = filter(lambda x: rpm == x.split('\t')[0], lines)
            if not lst:
                log_info("Package %s is not installed" % rpm)
                not_applicable = 1

    if check_bin != "":
        binaries = check_bin.split(',')
        for binary in binaries:
            cmd = "which %s" % binary
            if utils.run_subprocess(cmd, print_output=False, shell=True) != 0:
                not_applicable = 1

    if not_applicable:
        exit_fail()


def solution_file(message):
    write_to_file(os.path.join(os.environ['CURRENT_DIRECTORY'], SOLUTION_FILE), "a+b", message)


def service_is_enabled(service_name):
    """Returns true if given service is enabled on any runlevel"""
    return_value = False
    lines = get_file_content(VALUE_CHKCONFIG, "rb", True)
    for line in lines:
        if re.match('^%s.*:on' % service_name, line):
            return_value = True
            break
    return return_value


def config_file_changed(config_file_name):
    """
    Searches cached data in VALUE_CONFIGCHANGED

    returns:
    True if given config file has been changed
    False if given config file hasn't been changed
    """
    config_changed = False
    try:
        lines = get_file_content(VALUE_CONFIGCHANGED, "rb", True)
        for line in lines:
            if line.find(config_file_name) != -1:
                config_changed = True
                break
    except:
        pass
    return config_changed


def backup_config_file(config_file_name):
    """Copies specified file into VALUE_TMP_PREUPGRADE, keeping file structure"""
    try:
        # report error if file doesn't exist
        if not os.path.isfile(config_file_name):
            return 1

        # don't do anything if config file was not changed
        if not config_file_changed(config_file_name):
            return 2

        # stripping / from beginning is necessary to concat paths properly
        os.mkdir(os.path.join(VALUE_TMP_PREUPGRADE, os.path.dirname(config_file_name.strip("/"))))
    except OSError:
        # path probably exists, it's ok
        pass
    shutil.copyfile(config_file_name, os.path.join(VALUE_TMP_PREUPGRADE, config_file_name.strip("/")))

shorten_envs()
