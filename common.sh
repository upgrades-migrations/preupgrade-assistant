
CACHE=/var/cache/preupgrade
PREUPGRADE_CACHE=/var/cache/preupgrade/common
PREUPGRADE_CONFIG=/etc/preupgrade-assistant.conf
VALUE_RPM_QA=$PREUPGRADE_CACHE/rpm_qa.log
VALUE_ALL_CHANGED=$PREUPGRADE_CACHE/rpm_Va.log
VALUE_CONFIGCHANGED=$PREUPGRADE_CACHE/rpm_etc_Va.log
VALUE_PASSWD=$PREUPGRADE_CACHE/passwd.log
VALUE_CHKCONFIG=$PREUPGRADE_CACHE/chkconfig.log
VALUE_GROUP=$PREUPGRADE_CACHE/group.log
VALUE_RPMTRACKEDFILES=$PREUPGRADE_CACHE/rpmtrackedfiles.log
VALUE_RPM_RHSIGNED=$PREUPGRADE_CACHE/rpm_rhsigned.log
VALUE_ALLMYFILES=$PREUPGRADE_CACHE/allmyfiles.log
VALUE_EXECUTABLES=$PREUPGRADE_CACHE/executable.log
VALUE_TMP_PREUPGRADE=$XCCDF_VALUE_TMP_PREUPGRADE
POSTUPGRADE_DIR=$VALUE_TMP_PREUPGRADE/postupgrade.d
CURRENT_DIRECTORY=$XCCDF_VALUE_CURRENT_DIRECTORY
MIGRATE=$XCCDF_VALUE_MIGRATE
UPGRADE=$XCCDF_VALUE_UPGRADE
SOLUTION_FILE=$CURRENT_DIRECTORY/$XCCDF_VALUE_SOLUTION_FILE
KICKSTART_README=$VALUE_TMP_PREUPGRADE/kickstart/README

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
log()
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

log_debug()
{
    log "DEBUG" "$@"
}

log_info()
{
    log "INFO" "$@"
}

log_error()
{
    log "ERROR" "$@"
}

log_warning()
{
    log "WARNING" "$@"
}

log_risk()
{
    echo "INPLACERISK: $1: $2" >&2
}

log_none_risk()
{
    log_risk "NONE" "$1"
}

log_slight_risk()
{
    log_risk "SLIGHT" "$1"
}

log_medium_risk()
{
    log_risk "MEDIUM" "$1"
}

log_high_risk()
{
    log_risk "HIGH" "$1"
}

log_extreme_risk()
{
    log_risk "EXTREME" "$1"
}

exit_unknown()
{
    exit $RESULT_UNKNOWN
}

exit_pass()
{
    exit $RESULT_PASS
}

exit_fail()
{
    exit $RESULT_FAIL
}

exit_error()
{
    exit $RESULT_ERROR
}

exit_not_applicable()
{
    exit $RESULT_NOT_APPLICABLE
}

exit_informational()
{
    exit $RESULT_INFORMATIONAL
}

exit_fixed()
{
    exit $RESULT_FIXED
}

switch_to_content()
{
    cd $CURRENT_DIRECTORY
}

check_applies_to()
{
    local RPM=1
    if [ -z "$1" ]
    then
        RPM=0
    else
        RPM_NAME=$1
    fi

    local NOT_APPLICABLE=0
    if [ $RPM -eq 1 ]; then
        RPM_NAME=`echo "$RPM_NAME" | tr "," " "`
        for pkg in $RPM_NAME
        do
            grep "^$pkg[[:space:]]" $VALUE_RPM_QA > /dev/null
            if [ $? -ne 0 ]; then
                log_info "Package $pkg is not installed"
                NOT_APPLICABLE=1
            fi
        done
    fi
    if [ $NOT_APPLICABLE -eq 1 ]; then
        exit_not_applicable
    fi
}

check_rpm_to()
{
    local RPM=1
    local BINARY=1
    if [ -z "$1" ]
    then
        RPM=0
    else
        RPM_NAME=$1
    fi

    if [ -z "$2" ]
    then
        BINARY=0
    else
        BINARY_NAME=$2
    fi


    local NOT_APPLICABLE=0
    if [ $RPM -eq 1 ]; then
        RPM_NAME=`echo "$RPM_NAME" | tr "," " "`
        for pkg in $RPM_NAME
        do
            grep "^$pkg[[:space:]]" $VALUE_RPM_QA > /dev/null
            if [ $? -ne 0 ]; then
                log_high_risk "Package $pkg is not installed"
                NOT_APPLICABLE=1
            fi
        done
    fi

    if [ $BINARY -eq 1 ]; then
        BINARY_NAME=`echo "$BINARY_NAME" | tr "," " "`
        for bin in $BINARY_NAME
        do
            which $bin > /dev/null 2>&1
            if [ $? -ne 0 ]; then
                log_high_risk "Binary $bin is not installed"
                NOT_APPLICABLE=1
            fi
        done
    fi


    if [ $NOT_APPLICABLE -eq 1 ]; then
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
    CONFIG_FILE=$1

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

space_trim() {
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
  _section=""
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


# here is parsed PA configuration
load_pa_configuration() {
  # this is main function for parsing
  [ -f "$PREUPGRADE_CONFIG" ] && [ -r "$PREUPGRADE_CONFIG" ] || {
    log_error "Configuration file $PREUPGRADE_CONFIG is missing or is not readable!"
    exit_error
  }
  _pa_conf="$(conf_get_section "$PREUPGRADE_CONFIG" "preupgrade-assistant")"
  [ -z "$_pa_conf" ] && {
    log_error "Can't load any configuration from section preupgrade-assistant!"
    exit_error
  }

  printf "%s\n" "$_pa_conf" | while read line; do
    tmp_option=$(space_trim "$(echo "$line" | cut -d "=" -f 1)")
    tmp_val=$(space_trim "$(echo "$line" | cut -d "=" -f 2-)")
    echo "$line -- $tmp_option - $tmp_val -"
    # HERE add your actions
    case $tmp_option in
      home_directory_file)
        HOME_DIRECTORY_FILE="$tmp_val"
        ;;
      user_config_file)
        USER_CONFIG_FILE=$([ "$tmp_val" == "enabled" ] && echo 1 || echo 0)
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

  _uconf_file="/home/$1/$HOME_DIRECTORY_FILE"
  [ -f "$_uconf_file" ] || return 0 # missing file in user's home dir is OK
  conf_get_section "$_uconf_file" "home-dirs"
}


load_pa_configuration
switch_to_content
