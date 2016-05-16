
CACHE=/var/cache/preupgrade
# Directory with logs gathered by preupgrade-assistant
PREUPGRADE_CACHE=/var/cache/preupgrade/common
# Preupgrade-assistant configuration file
PREUPGRADE_CONFIG=/etc/preupgrade-assistant.conf
# Full path log file with to all installed packages
VALUE_RPM_QA=$PREUPGRADE_CACHE/rpm_qa.log
# Full path log file with to all changed files
VALUE_ALL_CHANGED=$PREUPGRADE_CACHE/rpm_Va.log
# Full path to log file with all /etc changed configuration files
VALUE_CONFIGCHANGED=$PREUPGRADE_CACHE/rpm_etc_Va.log
# Full path to log file with all users gathered by getent
VALUE_PASSWD=$PREUPGRADE_CACHE/passwd.log
# Full path to log file with all services enabled/disabled on system.
VALUE_CHKCONFIG=$PREUPGRADE_CACHE/chkconfig.log
# Full path to log file with all groups gathered by getent
VALUE_GROUP=$PREUPGRADE_CACHE/group.log
# Full path to log file with all installed files
VALUE_RPMTRACKEDFILES=$PREUPGRADE_CACHE/rpmtrackedfiles.log
# Full path to log file with all Red Hat signed packages
VALUE_RPM_RHSIGNED=$PREUPGRADE_CACHE/rpm_rhsigned.log
# Full path to log file with all local files
VALUE_ALLMYFILES=$PREUPGRADE_CACHE/allmyfiles.log
# Full path to log file with all executable files
VALUE_EXECUTABLES=$PREUPGRADE_CACHE/executable.log
# Variable which referes to temporary directory directory provided by module
VALUE_TMP_PREUPGRADE=$XCCDF_VALUE_TMP_PREUPGRADE
# postupgrade directory used by in-place upgrades.
# Scripts mentioned there are executed automatically by redhat-upgrade-tool
POSTUPGRADE_DIR=$VALUE_TMP_PREUPGRADE/postupgrade.d
CURRENT_DIRECTORY=$XCCDF_VALUE_CURRENT_DIRECTORY
# MIGRATE means if preupg binary was used with `--mode migrate` parameter
# UPGRADE means if preupg binary was used with `--mode upgrade` parameter
# These modes are used if `--mode` is not used
MIGRATE=$XCCDF_VALUE_MIGRATE
UPGRADE=$XCCDF_VALUE_UPGRADE
# Variable which referes to solution file provided by module
SOLUTION_FILE=$CURRENT_DIRECTORY/$XCCDF_VALUE_SOLUTION_FILE
# Directory which is used for kickstart generation
KICKSTART_DIR=$VALUE_TMP_PREUPGRADE/kickstart
# README file which contains description about all files in kickstart directory
KICKSTART_README=$KICKSTART_DIR/README
# Directory with scripts which can be executed after installation by administrator
KICKSTART_SCRIPTS=$KICKSTART_DIR/scripts
# The same as above
KICKSTART_POSTUPGRADE=$KICKSTART_SCRIPTS
# Variable which refers to static data used by preupgrade-assistant and modules
COMMON_DIR=$XCCDF_VALUE_REPORT_DIR/common
DIST_NATIVE=$XCCDF_VALUE_DIST_NATIVE
# Variable which indicates DEVEL mode.
DEVEL_MODE=$XCCDF_VALUE_DEVEL_MODE
# Variable which contains file with packages add to the kickstart anyway
SPECIAL_PKG_LIST=$KICKSTART_DIR/special_pkg_list
# Postupgrade directory which is not executed automatically
# after an upgrade or migration
NOAUTO_POSTUPGRADE_D=$VALUE_TMP_PREUPGRADE/noauto_postupgrade.d
RESULT_PASS=$XCCDF_RESULT_PASS
RESULT_FAIL=$XCCDF_RESULT_FAIL
RESULT_FAILED=$RESULT_FAIL
RESULT_ERROR=$XCCDF_RESULT_ERROR
RESULT_UNKNOWN=$XCCDF_RESULT_UNKNOWN
RESULT_NOT_APPLICABLE=$XCCDF_RESULT_NOT_APPLICABLE
RESULT_FIXED=$XCCDF_RESULT_FIXED
RESULT_INFORMATIONAL=$XCCDF_RESULT_INFORMATIONAL

# variables set by PA config file #
HOME_DIRECTORY_FILE=""
USER_CONFIG_FILE=0

PREUPG_API_VERSION=1

export LC_ALL=C

# general logging function
# ------------------------
#
# log SEVERITY [COMPONENT] MESSAGE
#
# @SEVERITY: set it to one of INFO|ERROR|WARNING
# @COMPONENT: optional, relevant RHEL component
# @MESSAGE: message to be logged
#
# Note that if env variable $COMPONENT is defined, it may be omitted from
# parameters.
_log()
{
    SEVERITY=$1 ; shift
    if test -z "$COMPONENT"; then
        # only message was passed
        if test "$#" -eq 1; then
            COMPONENT='[unknown]'
        else
            COMPONENT=$1 ; shift
        fi
    else
        if test "$#" -eq 2; then
            shift
        fi
    fi

    echo "$SEVERITY $COMPONENT: $1"
}

#log_debug(message, component_arg=None) -> None
#
#log message to stdout with severity debug
#if you would like to change component temporary, you may pass it as argument
#
#verbose information, may help with script debugging
log_debug()
{
    _log "DEBUG" "$@"
}

#log_info(message, component_arg=None) -> None
#
#log message to stdout with severity info
#if you would like to change component temporary, you may pass it as argument
#
#informational message
log_info()
{
    _log "INFO" "$@"
}

#log_error(message, component=None) -> None

##log message to stdout with severity error
#if you would like to change component temporary, you may pass it as argument
#use this severity if your script found something severe
#
#which may cause malfunction on new system
log_error()
{
    _log "ERROR" "$@"
}

#log_warning(message, component_arg=None) -> None
#
#log message to stdout with severity warning
#if you would like to change component temporary, you may pass it as argument
#
#important finding, administrator of system should be aware of this
log_warning()
{
    _log "WARNING" "$@"
}

#log risk level to stderr
_log_risk()
{
    echo "INPLACERISK: $1: $2" >&2
}

#log_slight_risk(message)
#
#no issues found; although there are some unexplored areas
log_slight_risk()
{
    _log_risk "SLIGHT" "$1"
}

#log_medium_risk(message)
#
#inplace upgrade is possible; system after upgrade may be unstable
log_medium_risk()
{
    _log_risk "MEDIUM" "$1"
}

#log_high_risk(message)
#
#Administrator has to inspect and correct upgraded system so
#inplace upgrade can be used.
log_high_risk()
{
    _log_risk "HIGH" "$1"
}

#log_extreme_risk(message)
#
#Inplace upgrade is impossible.
log_extreme_risk()
{
    _log_risk "EXTREME" "$1"
}

#Could not tell what happened.
exit_unknown()
{
    exit $RESULT_UNKNOWN
}

#Test passed.
exit_pass()
{
    exit $RESULT_PASS
}

#The test failed.
#Moving to new release with this configuration will result in malfunction.
exit_fail()
{
    exit $RESULT_FAIL
}

#The test failed.
#Moving to new release with this configuration will result in malfunction.
exit_failed()
{
    exit $RESULT_FAIL
}

#An error occurred and test could not complete.
#
#(script failed while doing its job)
exit_error()
{
    exit $RESULT_ERROR
}

#Rule did not apply to test target. (e.g. package is not installed)
exit_not_applicable()
{
    exit $RESULT_NOT_APPLICABLE
}

#Rule has only informational output.
exit_informational()
{
    exit $RESULT_INFORMATIONAL
}

#Rule failed, but was later fixed.
exit_fixed()
{
    exit $RESULT_FIXED
}

#Function for switch to the content directory
_switch_to_content()
{
    cd $CURRENT_DIRECTORY
}

# Function checks if package is installed.
# Parameter is a package name which will be checked.
# Return: 0 - package is installed
#         1 - package is NOT installed
is_pkg_installed()
{
    grep -q "^$1[[:space:]]" $VALUE_RPM_QA || return 1
    return 0
}

#Function checks is package is installed and signed by Red Hat
# Parameter list of packages which will be checked. Module requires them.
#:return: 0 - package is installed and signed by Red Hat
#         exit_not_applicable - module will not be executed
check_applies_to()
{
    local RPM=1
    local RPM_NAME="$1"
    [ -z "$1" ] && RPM=0

    local NOT_APPLICABLE=0
    if [ $RPM -eq 1 ]; then
        RPM_NAME=$(echo "$RPM_NAME" | tr "," " ")
        for pkg in $RPM_NAME
        do
            is_pkg_installed "$pkg" && is_dist_native "$pkg" || {
                log_info "Package $pkg is not installed or it is not signed by Red Hat."
                NOT_APPLICABLE=1
            }
        done
    fi
    if [ $NOT_APPLICABLE -eq 1 ]; then
        exit_not_applicable
    fi
}

#Function checks if relevant package is installed
#and if relevant binary exists on the system.
# Function is needed from module point of view.
#:param $1: list of RPMs separated by comma
#:param $2: list of binaries separated by comma
#:return:
check_rpm_to()
{
    local RPM=1
    local BINARY=1
    local RPM_NAME=$1
    local BINARY_NAME=$2
    local NOT_APPLICABLE=0

    [ -z "$1" ] && RPM=0
    [ -z "$2" ] && BINARY=0


    if [ $RPM -eq 1 ]; then
        RPM_NAME=$(echo "$RPM_NAME" | tr "," " ")
        for pkg in $RPM_NAME
        do
            grep "^$pkg[[:space:]]" $VALUE_RPM_QA > /dev/null
            if [ $? -ne 0 ]; then
                log_high_risk "Package $pkg is not installed."
                NOT_APPLICABLE=1
            fi
        done
    fi

    if [ $BINARY -eq 1 ]; then
        BINARY_NAME=$(echo "$BINARY_NAME" | tr "," " ")
        for bin in $BINARY_NAME
        do
            which $bin > /dev/null 2>&1
            if [ $? -ne 0 ]; then
                log_high_risk "Binary $bin is not installed."
                NOT_APPLICABLE=1
            fi
        done
    fi


    if [ $NOT_APPLICABLE -eq 1 ]; then
        log_high_risk "Please, install all required packages (and binaries) and run preupg again to process check properly."
        exit_fail
    fi
}

# This check can be used if you need root privilegues
check_root()
{
    if [ "$(id -u)" != "0" ]; then
        log_error "This script must be run as root"
        log_slight_risk "The script must be run as root"
        exit_error
    fi
}

#Function appends a message to solution file.
#solution file will be created in module directory
#:param message: Message - string of list of strings
solution_file()
{
    echo "$1" >> $SOLUTION_FILE
}


# returns true if service in $1 is enabled in any runlevel
service_is_enabled() {
    if [ $# -ne 1 ] ; then
        echo "Usage: service_is_enabled servicename"
        return 2
    fi
    grep -qe "^${1}.*:on" "$VALUE_CHKCONFIG" && return 0
    return 1
}

# backup the config file, returns:
# true if cp succeeds,
# 1 if config file doesn't exist
# 2 if config file was not changed and thus is not necessary to back-up
backup_config_file() {
    local CONFIG_FILE=$1

    # config file exists?
    if [ ! -f "$CONFIG_FILE" ] ; then
        return 1
    fi

    # config file is changed?
    grep -qe " ${CONFIG_FILE}" ${VALUE_CONFIGCHANGED} || return 2

    mkdir -p "${VALUE_TMP_PREUPGRADE}/$(dirname "$CONFIG_FILE")"
    cp -f "${CONFIG_FILE}" "${VALUE_TMP_PREUPGRADE}${CONFIG_FILE}"
    return $?
}

# Function trim spaces.
# parameter is string to trim
_space_trim() {
  echo "$@" | sed -r "s/^\s*(.*)\s*$/\1/"
}

# functions for easy parsing of config files
# returns 0 on success, otherwise 1
# requires path
conf_get_sections() {
  [ $# -eq 1 ] || return 1
  [ -f "$1" ] || return 1

  grep -E "^\[.+\]$" "$1" | sed -r "s/^\[(.+)\]$/\1/"
  return $?
}

# get all items from config file $1 inside section $2
# e.g.: conf_get_section CONFIG_FILE section-without-brackets
conf_get_section() {
  [ $# -eq 2 ] || return 1
  [ -f "$1" ] || return 1
  local _section=""

  while read line; do
    [ -z "$line" ] && continue
    echo "$line" | grep -q "^\[..*\]$" && {
      _section="$(echo "$line" | sed -E "s/^\[(.+)\]$/\1/")"
      continue # that's new section
    }
    [ -z "$_section" ] && continue

    #TODO: do not print comment lines?
    [ "$_section" == "$2" ] && echo "$line" |grep -vq "^#.*$" && echo "$line"
  done < "$1"

  return 0
}

# is_dist_native function return only 0 or 1
# return 1 if package is not installed and print warning log.
# Case DEVEL_MODE is turn off then return 0 if package is signed or 1 if not.
# Case DEVEL_MODE is turn on:
#   DIST_NATIVE = sign: return 0 if is RH_SIGNED else return 1
#   DIST_NATIVE = all: always return 0
#   DIST_NATIVE = path_to_file: return 0 if package is in file else return 1
is_dist_native()
{
    if [ $# -ne 1 ]; then
        return 1
    fi
    local pkg=$1

    grep "^$pkg[[:space:]]" $VALUE_RPM_QA > /dev/null
    if [ $? -ne 0 ]; then
        log_warning "Package $pkg is not installed on Red Hat Enterprise Linux system."
        return 1
    fi
    if [ x"$DEVEL_MODE" == "x0" ]; then
        grep "^$pkg[[:space:]]" $VALUE_RPM_RHSIGNED > /dev/null
        if [ $? -eq 0 ]; then
            return 0
        else
            return 1
        fi
    else
        case "$DIST_NATIVE" in
            "all")
                return 0
                ;;
            "sign")
                grep "^$pkg[[:space:]]" $VALUE_RPM_RHSIGNED > /dev/null
                if [ $? -eq 0 ]; then
                    return 0
                else
                    return 1
                fi
                ;;
            *)
                if [ -f "$DIST_NATIVE" ]; then
                    grep "^$pkg" $DIST_NATIVE > /dev/null
                    if [ $? -eq 0 ]; then
                        return 0
                    fi
                fi
                return 1
                ;;
        esac
    fi
}

# return list of all dist native packages according to is_dist_native()
get_dist_native_list() {
  local pkg
  while read line; do
    pkg=$(echo $line | cut -d " " -f1 )
    is_dist_native $pkg >/dev/null && echo $pkg
  done < "$VALUE_RPM_QA"
}

# here is parsed PA configuration
_load_pa_configuration() {
  # this is main function for parsing
  [ -f "$PREUPGRADE_CONFIG" ] && [ -r "$PREUPGRADE_CONFIG" ] || {
    log_error "Configuration file $PREUPGRADE_CONFIG is missing or is not readable!"
    exit_error
  }
  local _pa_conf="$(conf_get_section "$PREUPGRADE_CONFIG" "preupgrade-assistant")"
  local tmp_option
  local tmp_val

  [ -z "$_pa_conf" ] && {
    log_error "Can't load any configuration from section preupgrade-assistant!"
    exit_error
  }

  for line in $_pa_conf; do
    tmp_option=$(_space_trim "$(echo "$line" | cut -d "=" -f 1)")
    tmp_val=$(_space_trim "$(echo "$line" | cut -d "=" -f 2-)")
    # HERE add your actions
    case $tmp_option in
      home_directory_file)
        HOME_DIRECTORY_FILE="$tmp_val"
        ;;
      user_config_file)
        USER_CONFIG_FILE=$([ "$tmp_val" == "enabled" ] && echo 1 || echo 0)
        ;;
      dist_native)
        local temp="$tmp_val"
        ;;
      *) log_error "Unknown option $tmp_option"; exit_error
    esac
  done
}

# print items from [home-dirs] which are relevant for given user
# when username is not given or config file for user is not enabled,
# items from main configuration file is printed
# returns 0 on SUCCESS, otherwise 1 and logs warning
# shouldn't be used before load_config_parser
print_home_dirs() {
  [ $# -eq 1 ] && [ $USER_CONFIG_FILE -eq 1 ] || {
    conf_get_section "$PREUPGRADE_CONFIG" "home-dirs"
    return 0
  }

  local _uconf_file="/home/$1/$HOME_DIRECTORY_FILE"
  [ -f "$_uconf_file" ] || return 0 # missing file in user's home dir is OK
  conf_get_section "$_uconf_file" "home-dirs"
}

#Function adds a package to special_pkg_list
add_pkg_to_kickstart() {
  [ $# -eq 0  ] && {
    log_debug "Missing parameters! Any package will be added." >&2
    return 1
  }

  while [ $# -ne 0 ]; do
    echo $1 >> "$SPECIAL_PKG_LIST"
    shift
  done
  return 0
}
_load_pa_configuration
_switch_to_content
