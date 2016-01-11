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

import os
import sys
import datetime
import re
import shutil
import ConfigParser
from preup import utils
from preup.utils import get_file_content, write_to_file
from preup import settings

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
    'is_dist_native',
    'print_home_dirs',
    'load_pa_configuration',
    'get_dist_native_list',

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
    'COMMON_DIR',
    'SOLUTION_FILE',
    'POSTUPGRADE_DIR',
    'KICKSTART_README',
    'MIGRATE',
    'UPGRADE',
    'HOME_DIRECTORY_FILE',
    'USER_CONFIG_FILE',
    'PREUPG_API_VERSION',
    'DEVEL_MODE',
    'DIST_NATIVE',
)

CACHE="/var/cache/preupgrade"
PREUPGRADE_CACHE=os.path.join(CACHE, "common")
PREUPGRADE_CONFIG = settings.PREUPG_CONFIG_FILE
VALUE_RPM_QA=os.path.join(PREUPGRADE_CACHE, "rpm_qa.log")
VALUE_ALLCHANGED=os.path.join(PREUPGRADE_CACHE, "rpm_Va.log")
VALUE_CONFIGCHANGED=os.path.join(PREUPGRADE_CACHE, "rpm_etc_Va.log")
VALUE_PASSWD=os.path.join(PREUPGRADE_CACHE, "passwd.log")
VALUE_CHKCONFIG=os.path.join(PREUPGRADE_CACHE, "chkconfig.log")
VALUE_GROUP=os.path.join(PREUPGRADE_CACHE, "group.log")
VALUE_RPMTRACKEDFILES=os.path.join(PREUPGRADE_CACHE, "rpmtrackedfiles.log")
VALUE_ALLMYFILES=os.path.join(PREUPGRADE_CACHE, "allmyfiles.log")
VALUE_EXECUTABLES=os.path.join(PREUPGRADE_CACHE, "executable.log")
VALUE_RPM_RHSIGNED=os.path.join(PREUPGRADE_CACHE, "rpm_rhsigned.log")
VALUE_TMP_PREUPGRADE=os.environ['XCCDF_VALUE_TMP_PREUPGRADE']
SOLUTION_FILE=os.environ['XCCDF_VALUE_SOLUTION_FILE']
try:
    MIGRATE = os.environ['XCCDF_VALUE_MIGRATE']
    UPGRADE = os.environ['XCCDF_VALUE_UPGRADE']
except KeyError:
    MIGRATE = 1
    UPGRADE = 1
try:
    DEVEL_MODE = os.environ['XCCDF_VALUE_DEVEL_MODE']
except KeyError:
    DEVEL_MODE = 0
try:
    DIST_NATIVE = os.environ['XCCDF_VALUE_DIST_NATIVE']
except KeyError:
    DIST_NATIVE = 0
POSTUPGRADE_DIR=os.path.join(VALUE_TMP_PREUPGRADE, "postupgrade.d")
KICKSTART_README=os.path.join(VALUE_TMP_PREUPGRADE, "kickstart", "README")
COMMON_DIR = os.path.join(os.environ['XCCDF_VALUE_REPORT_DIR'], "common")


HOME_DIRECTORY_FILE = ""
USER_CONFIG_FILE = 0

PREUPG_API_VERSION=1

component = "unknown"


################
# RISK LOGGING #
################

def log_risk(severity, message):
    """
    log risk level to stderr
    """
    sys.stderr.write("INPLACERISK: %s: %s\n" % (severity, message.encode(settings.defenc)))


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
    """
    log message to stdout
    """
    global component
    comp_show = component_arg or component
    #if not comp_show:
    #    raise Exception('Component name wasn\'t set up. Please do so with function set_component().')
    sys.stdout.write("%s %s: %s\n" % (severity, comp_show, message.encode(settings.defenc)))


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
    """
    make all the oscap's environemt variables shorter
    """
    envs = os.environ
    prefixes = ('XCCDF_VALUE_', 'XCCDF_RESULT_')
    for env_key, env_value in envs.items():
        for prefix in prefixes:
            if env_key.startswith(prefix):
                os.environ[env_key.replace(prefix, '')] = env_value


def set_component(c):
    """
    configure name of component globally (it will be used in logging)
    """
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
    An error occurred and test could not complete. (script failed while doing its job)
    """
    sys.exit(int(os.environ['XCCDF_RESULT_ERROR']))


def exit_pass():
    """
    Test passed.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_PASS']))


def exit_unknown():
    """
    Could not tell what happened.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_UNKNOWN']))


def exit_not_applicable():
    """
    Rule did not apply to test target. (e.g. package is not installed)
    """
    sys.exit(int(os.environ['XCCDF_RESULT_NOT_APPLICABLE']))


def exit_fixed():
    """
    Rule failed, but was later fixed.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_FIXED']))


def exit_informational():
    """
    Rule failed, but was later fixed.
    """
    sys.exit(int(os.environ['XCCDF_RESULT_INFORMATIONAL']))


def switch_to_content():
    """
    Function for switch to the content directory
    """
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
    """
    Returns true if given service is enabled on any runlevel
    """
    return_value = False
    lines = get_file_content(VALUE_CHKCONFIG, "rb", True)
    for line in lines:
        if re.match('^%s.*:on' % service_name, line):
            return_value = True
            break
    return return_value


def config_file_changed(config_file_name):
    """
    Searches cached data in VALUE_CONFIGCHANGED and returns:
    True if given config file has been changed
    False if given config file hasn't been changed
    """
    config_changed = False
    try:
        lines = get_file_content(VALUE_CONFIGCHANGED, "rb", True)
        for line in lines:
            if line.find(config_file_name) != -1:
                config_changed=True
                break
    except:
        pass
    return config_changed


def backup_config_file(config_file_name):
    """
    Copies specified file into VALUE_TMP_PREUPGRADE, keeping file structure
    """
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


def is_dist_native(pkg):
    """
    is_dist_native function return only True or False
    return False if package is not installed and of course information log.
    Case DEVEL_MODE is turn off then return True if package is signed or False if not.
    Case DEVEL_MODE is turn on:
    DIST_NATIVE = sign: return True if is RH_SIGNED else return False
    DIST_NATIVE = all: always return True
    DIST_NATIVE = path_to_file: return True if package is in file else return False
    """

    rpm_qa = get_file_content(VALUE_RPM_QA, "rb", True)
    found = [x for x in rpm_qa if x.startswith(pkg)]
    if not found:
        log_warning("Package %s is not installed on Red Hat Enterprise Linux system.")
        return False

    rpm_signed = get_file_content(VALUE_RPM_RHSIGNED, "rb", True)
    if int(DEVEL_MODE) == 0:
        found = [x for x in rpm_signed if x.startswith(pkg)]
        if found:
            return True
        else:
            return False
    else:
        if DIST_NATIVE == "all":
            return True
        if DIST_NATIVE == "sign":
            found = [x for x in rpm_signed if x.startswith(pkg)]
            if found:
                return True
            else:
                return False
        if os.path.exists(DIST_NATIVE):
            list_native = get_file_content(DIST_NATIVE)
            if pkg in list_native:
                return True
        return False

def get_dist_native_list():
    """
    returns list of all installed native packages
    """

    native_pkgs = []
    tmp = get_file_content(VALUE_RPM_QA, "rb", True)
    pkgs = [i.split("\t")[0] for i in tmp]
    for pkg in pkgs:
        if(is_dist_native(pkg) is True):
            native_pkgs.append(pkg)
    return native_pkgs


def load_pa_configuration():
    """ Loads preupgrade-assistant configuration file """
    global HOME_DIRECTORY_FILE
    global USER_CONFIG_FILE
    global RH_SIGNED_PKGS

    if not os.path.exists(PREUPGRADE_CONFIG):
        log_error("Configuration file $PREUPGRADE_CONFIG is missing or is not readable!")
        exit_error()

    config = ConfigParser.RawConfigParser()
    config.read(PREUPGRADE_CONFIG)
    section = 'preupgrade-assistant'
    home_option = 'home_directory_file'
    user_file = 'user_config_file'
    if config.has_section(section):
        if config.has_option(section, home_option):
            HOME_DIRECTORY_FILE = config.get(section, home_option)
        if config.has_option(section, user_file):
            USER_CONFIG_FILE = config.get(section, user_file)


def print_home_dirs(user_name=""):
    """ Loads preupgrade-assistant configuration file """
    if not os.path.exists(PREUPGRADE_CONFIG):
        log_error("Configuration file $PREUPGRADE_CONFIG is missing or is not readable!")
        exit_error()

    config = ConfigParser.RawConfigParser()
    home_section = 'home-dirs'
    try:
        if USER_CONFIG_FILE == 'enabled' and user_name == "":
            config.read(PREUPGRADE_CONFIG)
            return config.get(home_section, "dirs")
        user_home_dir = os.path.join('/home', user_name, HOME_DIRECTORY_FILE)
        if not os.path.exists(user_home_dir):
            return 0
        config.read(user_home_dir)
        if config.has_option(home_section, 'dirs'):
            return config.get(home_section, 'dirs')
        return None
    except ConfigParser.NoSectionError:
        pass
    except ConfigParser.NoOptionError:
        pass


load_pa_configuration()
shorten_envs()
