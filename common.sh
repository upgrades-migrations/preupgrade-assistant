
CACHE=/var/cache/preupgrade
PREUPGRADE_CACHE=/var/cache/preupgrade/common
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
function log
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

function log_debug
{
    log "DEBUG" "$@"
}

function log_info
{
    log "INFO" "$@"
}

function log_error
{
    log "ERROR" "$@"
}

function log_warning
{
    log "WARNING" "$@"
}

function log_risk
{
    echo "INPLACERISK: $1: $2" >&2
}

function log_none_risk
{
    log_risk "NONE" "$1"
}

function log_slight_risk
{
    log_risk "SLIGHT" "$1"
}

function log_medium_risk
{
    log_risk "MEDIUM" "$1"
}

function log_high_risk
{
    log_risk "HIGH" "$1"
}

function log_extreme_risk
{
    log_risk "EXTREME" "$1"
}

function exit_unknown
{
    exit $RESULT_UNKNOWN
}

function exit_pass
{
    exit $RESULT_PASS
}

function exit_fail
{
    exit $RESULT_FAIL
}

function exit_error
{
    exit $RESULT_ERROR
}

function exit_not_applicable
{
    exit $RESULT_NOT_APPLICABLE
}

function exit_informational
{
    exit $RESULT_INFORMATIONAL
}

function exit_fixed
{
    exit $RESULT_FIXED
}

function switch_to_content
{
    cd $CURRENT_DIRECTORY
}

function check_applies_to
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

function check_rpm_to
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
function check_root
{
    if [ "$(id -u)" != "0" ]; then
        log_error "This script must be run as root"
        log_slight_risk "The script must be run as root"
        exit_error
    fi
}

function solution_file
{
    echo "$1" >> $SOLUTION_FILE
}


# returns true if service in $1 is enabled in any runlevel
function service_is_enabled {
    if [ $# -ne 1 ] ; then
        echo "Usage: service_is_enabled servicename"
        return 2
    fi
    if grep -e "^${1}.*:on" "$VALUE_CHKCONFIG" &>/dev/null ; then
        return 0
    fi
    return 1
}

# backup the config file, returns:
# true if cp succeeds,
# 1 if config file doesn't exist
# 2 if config file was not changed and thus is not necessary to back-up
function backup_config_file {
    CONFIG_FILE=$1

    # config file exists?
    if [ ! -f $CONFIG_FILE ] ; then
        return 1
    fi

    # config file is changed?
    if ! grep -e " ${CONFIG_FILE}" ${VALUE_CONFIGCHANGED} >/dev/null; then
        return 2
    fi

    mkdir -p "${VALUE_TMP_PREUPGRADE}/$(dirname $CONFIG_FILE)"
    cp -f "${CONFIG_FILE}" "${VALUE_TMP_PREUPGRADE}${CONFIG_FILE}"
    return $?
}

switch_to_content
