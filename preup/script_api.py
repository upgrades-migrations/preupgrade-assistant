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
import ConfigParser

from preup import settings
from preup.utils import FileHelper, ProcessHelper

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
    'get_dist_native_list',
    'get_cached',
    'add_pkg_to_kickstart',
    'add_postupgrade',
    'add_manual_postupgrade',

    'PREUPGRADE_CACHE',
    'VALUE_RPM_QA',
    'PREUPG_RPM_QA',
    'VALUE_ALLCHANGED',
    'PREUPG_ALLCHANGED'
    'VALUE_CONFIGCHANGED',
    'PREUPG_CONFIGCHANGED',
    'VALUE_PASSWD',
    'PREUPG_PASSWD',
    'VALUE_CHKCONFIG',
    'PREUPG_CHKCONFIG',
    'VALUE_GROUP',
    'PREUPG_GROUP',
    'VALUE_RPMTRACKEDFILES',
    'PREUPG_RPMTRACKEDFILES',
    'VALUE_ALLMYFILES',
    'PREUPG_ALLMYFILES',
    'VALUE_EXECUTABLES',
    'PREUPG_EXECUTABLES',
    'VALUE_RPM_RHSIGNED',
    'PREUPG_RPM_RHSIGNED',
    'VALUE_TMP_PREUPGRADE',
    'PREUPG_TMP_PREUPGRADE',
    'MODULE_NAME',
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
    'NOAUTO_POSTUPGRADE_D'
    'CONFID_FILES_DIR',
)

CACHE = "/var/cache/preupgrade"
PREUPGRADE_CACHE = os.path.join(CACHE, "common")
PREUPGRADE_CONFIG = settings.PREUPG_CONFIG_FILE
VALUE_RPM_QA = os.path.join(PREUPGRADE_CACHE, "rpm_qa.log")
PREUPG_RPM_QA = VALUE_RPM_QA
VALUE_ALLCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_Va.log")
PREUPG_ALLCHANGED = VALUE_ALLCHANGED
VALUE_CONFIGCHANGED = os.path.join(PREUPGRADE_CACHE, "rpm_etc_Va.log")
PREUPG_CONFIGCHANGED = VALUE_CONFIGCHANGED
VALUE_PASSWD = os.path.join(PREUPGRADE_CACHE, "passwd.log")
PREUPG_PASSWD = VALUE_PASSWD
VALUE_CHKCONFIG = os.path.join(PREUPGRADE_CACHE, "chkconfig.log")
PREUPG_CHKCONFIG = VALUE_CHKCONFIG
VALUE_GROUP = os.path.join(PREUPGRADE_CACHE, "group.log")
PREUPG_GROUP = VALUE_GROUP
VALUE_RPMTRACKEDFILES = os.path.join(PREUPGRADE_CACHE, "rpmtrackedfiles.log")
PREUPG_RPMTRACKEDFILES = VALUE_RPMTRACKEDFILES
VALUE_ALLMYFILES = os.path.join(PREUPGRADE_CACHE, "allmyfiles.log")
PREUPG_ALLMYFILES = VALUE_ALLMYFILES
VALUE_EXECUTABLES = os.path.join(PREUPGRADE_CACHE, "executable.log")
PREUPG_EXECUTABLES = VALUE_EXECUTABLES
VALUE_RPM_RHSIGNED = os.path.join(PREUPGRADE_CACHE, "rpm_rhsigned.log")
PREUPG_RPM_RHSIGNED = VALUE_RPM_RHSIGNED
VALUE_TMP_PREUPGRADE = os.environ['XCCDF_VALUE_TMP_PREUPGRADE']
PREUPG_TMP_PREUPGRADE = VALUE_TMP_PREUPGRADE
SOLUTION_FILE = os.environ['XCCDF_VALUE_SOLUTION_FILE']
CONFIG_FILES_DIR = os.path.join(PREUPG_TMP_PREUPGRADE, "config_files")

try:
    MODULE_NAME = os.environ['XCCDF_VALUE_MODULE_NAME']
except KeyError:
    MODULE_NAME = "MODULE_NAME"
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
    DIST_NATIVE = 'sign'
POSTUPGRADE_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "postupgrade.d")
PREUPG_POSTUPGRADE_DIR = POSTUPGRADE_DIR
KICKSTART_DIR = os.path.join(VALUE_TMP_PREUPGRADE, "kickstart")
KICKSTART_README = os.path.join(KICKSTART_DIR, "README")
KICKSTART_SCRIPTS = os.path.join(KICKSTART_DIR, "scripts")
KICKSTART_POSTUPGRADE = KICKSTART_SCRIPTS
COMMON_DIR = os.path.join(os.environ['XCCDF_VALUE_REPORT_DIR'], "common")
SPECIAL_PKG_LIST = os.path.join(KICKSTART_DIR, 'special_pkg_list')
NOAUTO_POSTUPGRADE_D = os.path.join(VALUE_TMP_PREUPGRADE, 'noauto_postupgrade.d')

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
    print("%s %s: %s\n" % (severity, comp_show, message.encode(settings.defenc)), end="", file=sys.stderr)


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


def _get_cached_command(command):
    # Function gets a cached command
    # input parameter is command provided by get_cached function
    lines = []
    if not os.path.exists(command):
        log_error("File $command does not exist. It is mandatory.")
    else:
        lines = FileHelper.get_file_content(command)
    return lines


def get_cached(command, key):
    # Get general system information from cache
    # Usage:    get_cached (file,<passwd,group>)
    #           get_cached (command, <rpm_qa, rpm_Va, rpm_etc_Va, chconfig>)
    #           get_cached (filelist, <executable, allmyfiles, rpmrhsignedfiles, rpmtrackedfiles>)
    if command == "file":
        if key == "passwd":
            if not os.path.exists(PREUPG_PASSWD):
                log_error("File %s does not exist. It is mandatory." % PREUPG_PASSWD )
                return 1
            else:
                return FileHelper.get_file_content(PREUPG_PASSWD)
        if key == "group":
            if not os.path.exists(PREUPG_GROUP):
                log_error("File %s does not exist. It is mandatory." % PREUPG_GROUP)
                return 1
            else:
                return FileHelper.get_file_content(PREUPG_GROUP)
        log_error("Unknown %s for %s . Supported are 'passwd', 'group'." % (key, command))
        return 1
    if command == "command":
        if key == "rpm_qa":
            return _get_cached_command(PREUPG_RPM_QA)
        if key == "rpm_Va":
            return _get_cached_command (PREUPG_ALLCHANGED)
        if key == "rpm_etc_Va":
            return _get_cached_command (PREUPG_CONFIGCHANGED)
        if key == "chconfig":
            return _get_cached_command (PREUPG_CHKCONFIG)
        log_error("Unknown $key for $command. Supported are 'rpm_qa', 'rpm_Va', 'rpm_etc_Va', 'chkconfig'.")
        return 1
    if command == "filelist":
        if key == "allmyfiles":
            return _get_cached_command (PREUPG_ALLMYFILES)
        if key == "executables":
            return _get_cached_command (PREUPG_EXECUTABLES)
        if key == "rpmtrackedfiles":
            return _get_cached_command (PREUPG_RPMTRACKEDFILES)
        if key == "rpmrhsignedfiles":
            return _get_cached_command (PREUPG_RPM_RHSIGNED)
        log_error("Unknown %s for %s. Supported are 'executable', 'allmyfiles','rpmtrackedfiles','rpmrhsignedfiles'." %(key, command))
        return 1
    if command == "info":
        log_error("This is not implemented yet")
        return 1
    log_error("Unknown command %s. Supported are 'file', 'command', filelist', 'info'." % command)
    return 1


def add_postupgrade(filename):
    # Add postupgrade script to /root/preupgrade/postupgrade.d directory
    # File as first parameter has to exists in modules directory
    # Usage:    add_postupgrade (file)

    postupgrade_name = os.path.join(PREUPG_POSTUPGRADE_DIR, os.path.basename(filename))
    if not os.path.exists(filename):
        log_error("%s does not exist" % filename )
        exit_error()
    if os.path.exists(postupgrade_name):
        log_warning("%s already exists in %s" % (os.path.basename(filename), PREUPG_POSTUPGRADE_DIR))
    shutil.copyfile(filename, postupgrade_name)


def add_manual_postupgrade(filename):
    # Add postupgrade script to /root/preupgrade/noauto_postupgrade.d directory
    # File as first parameter has to exists in modules directory
    # Usage:    add_manual_postupgrade (file)

    postupgrade_name = os.path.join(NOAUTO_POSTUPGRADE_D, os.path.basename(filename))
    if not os.path.exists(filename):
        log_error("%s does not exist" % filename )
        exit_error()
    if os.path.exists(postupgrade_name):
        log_warning("%s already exists in %s" % (os.path.basename(filename), NOAUTO_POSTUPGRADE_D))
    shutil.copyfile(filename, postupgrade_name)


def add_to_kickstart_readme(filename, description):
    # Add filename and description to /root/preupgrade/kickstart/README file
    # Filename as first parameter which will be inserted into README file
    # Description of filename as second parameter which will be inserted into README file.
    # Format in README file is:
    # * <filename> - <description>
    # Usage:    add_to_kickstart_readme (<filename>, <description>)
    line = " * %s - %s" % (filename, description)
    FileHelper.write_to_file(KICKSTART_README, "a+b", line)


def _check_config_file(conf_file_type, conf_file):
    full_path = os.path.join(CONFIG_FILES_DIR, conf_file_type, conf_file)
    if os.path.exists(full_path):
        log_warning("File '%s' already exists in %s directory." % (conf_file,
                                                                   os.path.join(CONFIG_FILES_DIR, conf_file_type)))
        return True
    return False


def add_config_file(config_type, filename):

    # Add config file to /root/preupgrade/{clean,dirty,etc} directory
    # First paramater is configuration directory where we want to store a file.
    #
    # second parameter is a file which we store
    # Usage:    add_config_file <clean,dirty> <full_path_file_name>

    if not config_type:
        log_error("Missing configuration type directory.")
        return 1
    if not filename:
        log_error("Missing full_path_file name.")
    dirty_name = "dirty"
    clean_name = "clean"
    unchecked_name = "unchecked"
    deprecated_name = "deprecated"
    clean_dir = os.path.join(CONFIG_FILES_DIR, clean_name)
    dirty_dir = os.path.join(CONFIG_FILES_DIR, dirty_name)
    unchecked_dir = os.path.join(CONFIG_FILES_DIR, unchecked_name)
    backup_file= os.path.join(CONFIG_FILES_DIR, config_type, filename)
    message = "You want to store the file into %s directory."
    if config_type == clean_name:
            if _check_config_file(dirty_name, filename):
                log_warning(message % dirty_dir)
            if _check_config_file(config_type, filename):
                return 1
    elif config_type == dirty_name:
            if _check_config_file(clean_name, filename):
                log_warning(message % clean_dir)
            if _check_config_file(config_type, filename):
                return 1
    elif config_type == unchecked_name:
            if _check_config_file(clean_name, filename):
                log_warning(message % clean_dir)
            if _check_config_file(dirty_name, filename):
                log_warning(message % dirty_dir)
            if _check_config_file(config_type, filename):
                return 1
    elif config_type == deprecated_name:
            if _check_config_file(clean_name, filename):
                log_warning(message % clean_dir)
            if _check_config_file(dirty_name, filename):
                log_warning(message % dirty_dir)
            if _check_config_file(unchecked_name, filename):
                log_warning(message % unchecked_dir)
            if _check_config_file(config_type, filename):
                return 1
    else:
        log_error("Unknown '%s' option in function add_config_file." % config_type)
        log_error("Allowed options are <clean,dirty,unchecked,deprecated>.")
        return 1

    dir_name = os.path.dirname(backup_file)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    shutil.copy(filename, backup_file)
    return 0


def add_kickstart_dir(filename):
    # Add filename /root/preupgrade/kickstart directory
    # File as first parameter has to exists in modules directory
    # Usage:    add_to_kickstart_dir (filename, description)
    kickstart_name = os.path.join(KICKSTART_DIR, os.path.basename(filename))
    if not os.path.exists(filename):
        log_error("%s does not exist" % filename )
        exit_error()
    if os.path.exists(kickstart_name):
        log_warning("%s already exists in %s" % (os.path.basename(filename), KICKSTART_DIR))
    shutil.copyfile(filename, kickstart_name)


def get_option(option):
    # Get option set up by preupgrade-assistant
    # Available options are <migration, upgrade>
    # Usage:    get_option (option)
    # Returns:  0,1

    if option == "migration":
        return MIGRATE
    if option == "upgrade":
        return UPGRADE
    log_error("Supported options are 'migration', 'upgrade'.")

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


def is_pkg_installed(pkg_name):
    lines = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
    found = [x for x in lines if x.split()[0] == pkg_name]
    if found:
        return True
    else:
        return False


def check_applies_to(check_applies=""):
    not_applicable = 0
    if check_applies != "":
        rpms = check_applies.split(',')
        for rpm in rpms:
            if not (is_pkg_installed(rpm) and is_dist_native(rpm)):
                log_info("Package %s is not installed or it is not signed by Red Hat." % rpm)
                not_applicable = 1
    if not_applicable:
        exit_not_applicable()


def check_rpm_to(check_rpm="", check_bin=""):
    not_applicable = 0

    if check_rpm != "":
        rpms = check_rpm.split(',')
        lines = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
        for rpm in rpms:
            lst = filter(lambda x: rpm == x.split('\t')[0], lines)
            if not lst:
                log_info("Package %s is not installed." % rpm)
                not_applicable = 1

    if check_bin != "":
        binaries = check_bin.split(',')
        for binary in binaries:
            cmd = "which %s" % binary
            if ProcessHelper.run_subprocess(cmd, print_output=False, shell=True) != 0:
                log_info("Binary %s is not installed." % binary)
                not_applicable = 1

    if not_applicable:
        log_high_risk("Please, install all required packages (and binaries) and run preupg again to process check properly.")
        exit_fail()


def solution_file(message):
    FileHelper.write_to_file(os.path.join(os.environ['CURRENT_DIRECTORY'], SOLUTION_FILE), "a+b", message)


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
            list_native = FileHelper.get_file_content(DIST_NATIVE)
            if pkg in list_native:
                return True
        return False


def get_dist_native_list():
    """
    returns list of all installed native packages
    """

    native_pkgs = []
    tmp = FileHelper.get_file_content(VALUE_RPM_QA, "rb", True)
    pkgs = [i.split("\t")[0] for i in tmp]
    for pkg in pkgs:
        if is_dist_native(pkg) is True:
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

    config = ConfigParser.RawConfigParser(allow_no_value=True)
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

    config = ConfigParser.RawConfigParser(allow_no_value=True)
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
    except ConfigParser.NoSectionError:
        pass
    except ConfigParser.NoOptionError:
        pass


def add_pkg_to_kickstart(pkg_name):
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
    for pkg in pkg_name.split():
        FileHelper.write_to_file(SPECIAL_PKG_LIST, "a+b", pkg)
    return 0


load_pa_configuration()

shorten_envs()
