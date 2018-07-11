# -*- coding: utf-8 -*-
"""
python API for content writers

USAGE
*****

Best way is to import all functions from this module:

from script_api import *

These functions are available:

* logging functions -- log_*
 * log message to stdout
* logging risk functions -- log_*_risk
 * log risk level -- so administrator know how risky is to inplace upgrade
* get_dest_dir -- get dir for storing configuration files
* exit_* -- terminate execution with appropriate exit code
"""

from __future__ import unicode_literals, print_function
import os
import sys
import re
import shutil
import errno
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from preupg import settings
from preupg.utils import FileHelper, ProcessHelper

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

    'exit_error',
    'exit_fail',
    'exit_fixed',
    'exit_informational',
    'exit_not_applicable',
    'exit_informational',
    'exit_pass',
    'check_rpm_to',
    'check_applies_to',
    'solution_file',
    'switch_to_content',
    'service_is_enabled',
    'is_dist_native',
    'get_dist_native_list',
    'is_pkg_installed',
    'add_pkg_to_kickstart',
    'deploy_hook',

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
    'MODULE_PATH',
    'COMMON_DIR',
    'SOLUTION_FILE',
    'POSTUPGRADE_DIR',
    'KICKSTART_DIR',
    'KICKSTART_README',
    'KICKSTART_SCRIPTS',
    'KICKSTART_POSTUPGRADE',
    'MIGRATE',
    'UPGRADE',
    'HOME_DIRECTORY_FILE',
    'USER_CONFIG_FILE',
    'PREUPG_API_VERSION',
    'DEVEL_MODE',
    'DIST_NATIVE',
    'SPECIAL_PKG_LIST',
    'NOAUTO_POSTUPGRADE_D',
)

# These variables and functions will be available
# for Bash preupgrade-assistant modules.
#

CACHE = "/var/cache/preupgrade"

#
# Directory with logs gathered by preupgrade-assistant
#
PREUPGRADE_CACHE = os.path.join(CACHE, "common")

#
# Preupgrade-assistant configuration file
#
PREUPGRADE_CONFIG = settings.PREUPG_CONFIG_FILE

#
# Full path log file with to all installed packages
#
VALUE_RPM_QA = os.path.join(PREUPGRADE_CACHE, "rpm_qa.log")

#
# Full path log file with to all changed files
#
VALUE_ALLCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_Va.log")

#
# Full path to log file with all /etc changed configuration files
#
VALUE_CONFIGCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_etc_Va.log")

#
# Full path to log file with all users gathered by getent
#
VALUE_PASSWD = os.path.join(PREUPGRADE_CACHE, "passwd.log")

#
# Full path to log file with all services enabled/disabled on system.
#
VALUE_CHKCONFIG = os.path.join(PREUPGRADE_CACHE, "chkconfig.log")

#
# Full path to log file with all groups gathered by getent
#
VALUE_GROUP = os.path.join(PREUPGRADE_CACHE, "group.log")

#
# Full path to log file with all installed files
#
VALUE_RPMTRACKEDFILES = os.path.join(PREUPGRADE_CACHE, "rpmtrackedfiles.log")

#
# Full path to log file with all installed files
#
VALUE_ALLMYFILES = os.path.join(PREUPGRADE_CACHE, "allmyfiles.log")

#
# Full path to log file with all executable files
#
VALUE_EXECUTABLES = os.path.join(PREUPGRADE_CACHE, "executable.log")

#
# Full path to log file with all Red Hat signed packages
#
VALUE_RPM_RHSIGNED = os.path.join(PREUPGRADE_CACHE, "rpm_rhsigned.log")

#
# Variable which referes to temporary directory directory provided by module
#
VALUE_TMP_PREUPGRADE = os.environ['XCCDF_VALUE_TMP_PREUPGRADE']

#
# Directory with configuration files that can be applied safely.
#
# Configuration files in this directory will be automatically applied on the
# upgraded system. Files has to be stored in this directory using whole path
# referring to the place where they should be copied. E.g.:
#   $CLEANCONF_DIR/etc/group -> /etc/group
#
CLEANCONF_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "cleanconf")

#
# Directory with configuration files that need to be overviewed manually.
#
# Configuration files in this directory cannot be applied on the upgraded
# system safely and need to be handled or overviewed manually. Usually are not
# copied automatically on the upgraded system unless there is a post-upgrade
# script that handle issue related with a configuration file at least
# partially.
#
DIRTYCONF_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "dirtyconf")

#
# Variable which referes to current directory directory provided by module
#
VALUE_CURRENT_DIRECTORY = os.environ['XCCDF_VALUE_CURRENT_DIRECTORY']

#
# Variable which referes to solution file provided by module
#
SOLUTION_FILE = os.path.join(VALUE_CURRENT_DIRECTORY, settings.solution_txt)

#
# Variable which referes to current upgrade path directory
#
VALUE_REPORT_DIR = os.environ['XCCDF_VALUE_REPORT_DIR']

#
# Name of module being currently executed
#
try:
    MODULE_PATH = os.environ['XCCDF_VALUE_MODULE_PATH']
except KeyError:
    MODULE_PATH = VALUE_CURRENT_DIRECTORY.replace(VALUE_REPORT_DIR, '')
    MODULE_PATH = MODULE_PATH.replace('/', '_')


#
# MIGRATE means if preupg binary was used with `--mode migrate` parameter
# UPGRADE means if preupg binary was used with `--mode upgrade` parameter
# These modes are used if `--mode` is not used
#
try:
    MIGRATE = os.environ['XCCDF_VALUE_MIGRATE']
    UPGRADE = os.environ['XCCDF_VALUE_UPGRADE']
except KeyError:
    MIGRATE = 1
    UPGRADE = 1

#
# Variable which indicates DEVEL mode.
#
try:
    DEVEL_MODE = os.environ['XCCDF_VALUE_DEVEL_MODE']
except KeyError:
    DEVEL_MODE = 0

#
# Override mode for is_dist_native() and similar
#
# Affects which packages are considered native:
#
# If set to 'sign' (default), GPG signature is consulted.  If 'all',
# all packages are native.  If set to path to a file, packages listed
# there are native.
#
try:
    DIST_NATIVE = os.environ['XCCDF_VALUE_DIST_NATIVE']
except KeyError:
    DIST_NATIVE = 'sign'

#
# preupgrade-scripts directory used by redhat-upgrade-tool
#
# Executable scripts inside the directrory (ans subdirectories) are processed
# by redhat-upgrade-tool during the pre-upgrade phase, after the upgrade RPM
# transaction is calculated and before the reboot is processed.
#
PREUPGRADE_SCRIPT_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "preupgrade-scripts")

#
# postupgrade directory used by in-place upgrades.
#
# Scripts mentioned there are executed automatically by redhat-upgrade-tool
#
POSTUPGRADE_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "postupgrade.d")

#
# postmigrate directory used after migration
#
# Executable scripts in the directory are processed during the %post phase
# when migration to the new system is done using the generated kickstart file.
#
POSTMIGRATE_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "postmigrate.d")

#
# Directory which is used for kickstart generation
#
KICKSTART_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "kickstart")

#
# README file which contains description about all files in kickstart directory
#
KICKSTART_README = os.path.join(KICKSTART_DIR, "README")

#
# Directory with scripts which can be executed after installation by administrator
#
KICKSTART_SCRIPTS = os.path.join(KICKSTART_DIR, "scripts")

#
# The same as $KICKSTART_SCRIPTS
#
KICKSTART_POSTUPGRADE = KICKSTART_SCRIPTS

#
# Variable which refers to static data used by preupgrade-assistant and modules
#
COMMON_DIR = os.path.join(os.environ['XCCDF_VALUE_REPORT_DIR'], "common")

#
# Variable which contains file with packages add to the kickstart anyway
#
SPECIAL_PKG_LIST = os.path.join(KICKSTART_DIR, 'special_pkg_list')

#
# Postupgrade directory which is not executed automatically after an upgrade or migration
#
NOAUTO_POSTUPGRADE_D = os.path.join(VALUE_TMP_PREUPGRADE, 'noauto_postupgrade.d')

#
# variables set by PA config file #
#
HOME_DIRECTORY_FILE = ""
USER_CONFIG_FILE = 0

#
# Version of this API
#
PREUPG_API_VERSION = 1

################
# RISK LOGGING #
################

def _log_risk(severity, message):
    """
    log risk level to stderr
    """
    print("preupg.risk.%s: %s\n" % (severity, message.encode(settings.defenc)), end="", file=sys.stderr)


def log_extreme_risk(message):
    """
    log_extreme_risk(message)

    Inplace upgrade is impossible.
    """
    _log_risk("EXTREME", message)


def log_high_risk(message):
    """
    log_high_risk(message)

    Administrator has to inspect and correct upgraded system so
    inplace upgrade can be used.
    """
    _log_risk("HIGH", message)


def log_medium_risk(message):
    """
    log_medium_risk(message)

    inplace upgrade is possible; system after upgrade may be unstable
    """
    _log_risk("MEDIUM", message)


def log_slight_risk(message):
    """
    log_slight_risk(message)

    no issues found; although there are some unexplored areas
    """
    _log_risk("SLIGHT", message)


##################
# STDOUT LOGGING #
##################

def _log(severity, message):
    """
    general logging function

    :param severity: set it to one of INFO|ERROR|WARNING
    :param message:message to be logged
    :return:
    """
    print("preupg.log.%s: %s\n" % (severity, message.encode(settings.defenc)), end="", file=sys.stderr)


def log_error(message):
    """
    log_error(message) -> None

    log message to stdout with severity error

    use this severity if your script found something severe
    which may cause malfunction on new system
    """
    _log('ERROR', message)


def log_warning(message):
    """
    log_warning(message) -> None

    log message to stdout with severity warning

    important finding, administrator of system should be aware of this
    """
    _log('WARNING', message)


def log_info(message):
    """
    log_info(message) -> None

    log message to stdout with severity info

    informational message
    """
    _log('INFO', message)


def log_debug(message):
    """
    log_debug(message) -> None

    log message to stdout with severity debug

    verbose information, may help with script debugging
    """
    _log('DEBUG', message)


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


# These are shortcut functions for:
#   sys.exit(int(os.environ['FAIL']))

def exit_fail():
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


def is_pkg_installed(pkg_name):
    """
    Function checks if package is installed.

    :param pkg_name: Parameter is a package name which will be checked.
    :return: 0 - package is installed
             1 - package is NOT installed
    """
    lines = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
    found = [x for x in lines if x.split()[0] == pkg_name]
    if found:
        return True
    else:
        return False


def check_applies_to(check_applies=""):
    """
    Function checks is package is installed and signed by Red Hat

    :param check_applies: Parameter list of packages which will be checked. Module requires them.
    :return: 0 - package is installed and signed by Red Hat
             exit_not_applicable - module will not be executed
    """
    not_applicable = 0
    if check_applies != "":
        rpms = check_applies.split(',')
        for rpm in rpms:
            if not (is_pkg_installed(rpm) and is_dist_native(rpm)):
                log_info("Package %s is not installed or it is not signed by Red Hat." % rpm)
                not_applicable = 1
    if not_applicable:
        exit_not_applicable()
    return not_applicable


def check_rpm_to(check_rpm="", check_bin=""):
    """
    Function checks if relevant package is installed and if relevant binary exists on the system.

    Function is needed from module point of view.

    :param check_rpm: list of RPMs separated by comma
    :param check_bin: list of binaries separated by comma
    :return:
    """
    not_applicable = 0

    if check_rpm != "":
        rpms = check_rpm.split(',')
        lines = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
        for rpm in rpms:
            lst = [x for x in lines if rpm == x.split('\t')[0]]
            if not lst:
                log_high_risk("Package %s is not installed." % rpm)
                not_applicable = 1

    if check_bin != "":
        binaries = check_bin.split(',')
        for binary in binaries:
            cmd = "which %s" % binary
            if ProcessHelper.run_subprocess(cmd, print_output=False, shell=True) != 0:
                log_high_risk("Binary %s is not installed." % binary)
                not_applicable = 1

    if not_applicable:
        log_high_risk("Please, install all required packages (and binaries)"
                      " and run preupg again to process check properly.")
        exit_fail()
    return not_applicable


def solution_file(message):
    """
    Function appends a message to solution file.

    solution file will be created in module directory

    :param message: Message - string of list of strings
    :return:
    """
    if os.path.exists(SOLUTION_FILE):
        mod = "a+b"
    else:
        mod = "wb"
    FileHelper.write_to_file(SOLUTION_FILE, mod, message)


def service_is_enabled(service_name):
    """Returns true if given service is enabled on any runlevel"""
    return_value = False
    lines = FileHelper.get_file_content(VALUE_CHKCONFIG, "rb", True)
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
        lines = FileHelper.get_file_content(VALUE_CONFIGCHANGED, "rb", True)
        for line in lines:
            if line.find(config_file_name) != -1:
                config_changed = True
                break
    except:
        pass
    return config_changed


def backup_config_file(config_file_name):
    """
    backup the config file

    :param config_file_name:
    :return:
            true if cp succeeds,
            if config file doesn't exist
            2 if config file was not changed and thus is not necessary to back-up
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
    return 1 if package is not installed and print warning log.
    is_dist_native function return only True or False
    Case DEVEL_MODE is turn off then return True if package is signed or False if not.
    Case DEVEL_MODE is turn on:
    DIST_NATIVE = sign: return True if is RH_SIGNED else return False
    DIST_NATIVE = all: always return True
    DIST_NATIVE = path_to_file: return True if package is in file else return False
    """

    rpm_qa = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
    found = [x for x in rpm_qa if x.split()[0] == pkg]
    if not found:
        log_warning("Package %s is not installed on Red Hat Enterprise Linux system.")
        return False

    rpm_signed = FileHelper.get_file_content(VALUE_RPM_RHSIGNED, "rb", True)
    found = [x for x in rpm_signed if x.split()[0] == pkg]

    if int(DEVEL_MODE) == 0:
        if found:
            return True
        else:
            return False
    else:
        if DIST_NATIVE == "all":
            return True
        if DIST_NATIVE == "sign":
            if found:
                return True
            else:
                return False
        if os.path.exists(DIST_NATIVE):
            list_native = map(
                unicode.strip,
                FileHelper.get_file_content(DIST_NATIVE, "r", method=True)
            )
            if pkg in list_native:
                return True
        return False


def get_dist_native_list():
    """
    return list of all dist native packages according to is_dist_native()
    """

    native_pkgs = []
    tmp = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
    pkgs = [i.split("\t")[0] for i in tmp]
    for pkg in pkgs:
        if is_dist_native(pkg) is True:
            native_pkgs.append(pkg)
    return native_pkgs


def load_pa_configuration():
    """ this is main function for parsing """
    global HOME_DIRECTORY_FILE
    global USER_CONFIG_FILE
    global RH_SIGNED_PKGS

    if not os.path.exists(PREUPGRADE_CONFIG):
        log_error("Configuration file %s is missing or is not readable!"
                  % PREUPGRADE_CONFIG)
        exit_error()

    config = configparser.RawConfigParser()
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
    """
    print items from [home-dirs] which are relevant for given user

    when username is not given or config file for user is not enabled,
    items from main configuration file is printed
    returns 0 on SUCCESS, otherwise 1 and logs warning
    shouldn't be used before load_config_parser
    """
    if not os.path.exists(PREUPGRADE_CONFIG):
        log_error("Configuration file %s is missing or is not readable!"
                  % PREUPGRADE_CONFIG)
        exit_error()

    config = configparser.RawConfigParser()
    home_option = 'home-dirs'
    try:
        if USER_CONFIG_FILE == 'enabled' and user_name == "":
            config.read(PREUPGRADE_CONFIG)
            return config.options(home_option)
        user_home_dir = os.path.join('/home', user_name, HOME_DIRECTORY_FILE)
        if not os.path.exists(user_home_dir):
            return 0
        config.read(user_home_dir)
        return config.options(home_option)
    except configparser.NoSectionError:
        pass
    except configparser.NoOptionError:
        pass


def add_pkg_to_kickstart(pkg_name):
    """ Function adds a package to special_pkg_list """
    empty = False
    if isinstance(pkg_name, list):
        # list of packages
        if len(pkg_name) == 0:
            empty = True
    else:
        # string - pkg_name delimited by whitespace
        if len(pkg_name.strip()) == 0:
            empty = True
        else:
            # make list from string
            pkg_name = pkg_name.strip().split()
    if empty is True:
        log_debug("Missing parameters! Any package will be added.")
        return 1
    for pkg in pkg_name:
        FileHelper.write_to_file(SPECIAL_PKG_LIST, "a+b", pkg.strip() + '\n')
    return 0


def deploy_hook(*args):
    """
    Function which deploys script to specific location.

    :param hook: hook, like postupgrade, preupgrade, etc.
    :param script_name: script name
    :return:
    """

    if MODULE_PATH == "":
        return 0
    if len(args) < 1:
        log_error("Hook name is not specified. (Possible values are postupgrade, preupgrade.)")
        exit_error()
    elif len(args) < 2:
        log_error("Script name is not specified. It is mandatory.")
        exit_error()
    deploy_name = args[0]
    script_name = args[1]
    if deploy_name == "postupgrade" or deploy_name == "preupgrade":
        if not os.path.exists(script_name):
            log_error("Script_name %s does not exist." % script_name)
            exit_error()
        hook_dir = "%s/hooks/%s/%s" % (VALUE_TMP_PREUPGRADE, MODULE_PATH, deploy_name)
        if not os.path.isdir(hook_dir):
            os.makedirs(hook_dir)
        else:
            log_error("The %s directory already exists" % hook_dir)
            exit_error()
        try:
            shutil.copyfile(script_name, os.path.join(hook_dir, "run_hook"))
            for arg in args[2:]:
                if arg.startswith('/'):
                    hook_arg = os.path.join(hook_dir, os.path.basename(arg))
                else:
                    hook_arg = os.path.join(hook_dir, arg)
                if os.path.isdir(hook_arg):
                    log_error("The %s directory already exists" % hook_arg)
                    exit_error()
                if os.path.isfile(hook_arg):
                    log_error("The %s file already exists" % hook_arg)
                    exit_error()
                try:
                    shutil.copytree(arg, hook_arg)
                except OSError as exc:
                    if exc.errno == errno.ENOTDIR:
                        shutil.copyfile(arg, hook_arg)
                    else:
                        log_error("Copying failed: %s" % exc)
                        exit_error()
        except IOError as e:
            log_error("Copying of hook script failed: %s" % e)
            exit_error()

    else:
        log_error("Unknown hook option '%s'" % deploy_name)
        exit_error()

load_pa_configuration()

shorten_envs()

os.chdir(VALUE_CURRENT_DIRECTORY)
