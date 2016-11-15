#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

#
# The whole section above is processed and modified by preupg-xccdf-compose
# script, according to content of INI file (in this case content.ini).
# And in addition the LICENSE used by PreupgradeAssistant is inserted.
#

##
# Briefly:
#    When you want to fix an issue automatically, there are several ways what
#    you can do:
#      1) you can store modified config files to special directories to apply
#         them later on the new system
#      2) you can create executable script and store them to special directory,
#         so they will be executed during post-upgrade phase
#      - for both cases above: you should log message about done/planned action
#        - so use log_info or log_slight_risk
#      final) in case that there is not another issue and you fixes any,
#             exit by exit_fixed
##

##
# Story:
#
# Do you remember the previous example about required action? Could you
# imagine, that in such case (some option has been deprecated/removed on new
# system and should be removed from configuration file) we can do an action
# automatically? Of course under condition that we can do that safely.
#
# So this module will fix similar problem for naughty-foo package:
#  1) option "obsoleted_option" has been renamed on new system to "new_option"
#      - nice, this we can fix it in our config file safely!
#  2) second issue is about "deprecated_option", which should be removed
#     - we will just comment out such line, but in that case we should still
#       recommend inspection by user - because he may will need to modify
#       their's application because of the option is missing
#  3) we found that for correct functionality we need to install another one
#     package (for any reason - sometimes it is required in real world)
#     - this we can resolve simply by post-upgrade script and say that we
#       fixes that issue
#

###########################################################
# FUNCTIONS AND VARIABLES                                 #
###########################################################

#
# Special directory of Preupgrade Assistant, which should contains config
# files, that are compatible for upgrade or migration to new system
# and user doesn't have to check it. See manual.
#
PREUPG_CLEANCONFDIR="$VALUE_TMP_PREUPGRADE/cleanconf"

#
# path to config file
#
foo_conf="/etc/preupg-foo-example"

#
# path to backed up config file
#
dst_foo_conf="${PREUPG_CLEANCONFDIR}${foo_conf}"

#
# name of the post-upgrade script
#
post_script="04_fix_issue_postupgrade.sh"

#
# expected exit code
#
ret=$RESULT_PASS

#
# Set expected exit code according to given parameter and current value
# of the $ret variable
#
# @param  exit code; expted values are: $RESULT_FAIL, $RESULT_FIXED
#
set_result() {
  case $1 in
    $RESULT_FAIL)  ret=$1 ;;
    $RESULT_FIXED) [ $ret -ne $RESULT_FAIL ] && ret=$1 ;;
  esac
}


###########################################################
# MAIN                                                    #
###########################################################

if [[ ! -e "$foo_conf" ]]; then
  # The file is required, so log error and exit with error when it doesn't
  # exists.
  log_error "The $foo_conf file doesn't exist, but it is required by naughty-foo package."
  exit_error
fi

# case 1)
if grep -q "obsoleted_option" "$foo_conf"; then
  log_info "The 'obsoleted_option' in '$foo_conf' has been renamed on new system to 'new_option'."

  # fix it - store output file to special directory, keeping its parents
  # We will use $PREUPG_CLEANCONFDIR for this purpose (see above). However,
  # we should check that file hasn't been backed up already at first.
  # (We assume now, that everything else is compatible. Otherwise we should
  #  not use that directory and use dirtyconf instead.)
  [ -e "$dst_foo_conf" ] \
    || cp -ar "$foo_conf" "$PREUPG_CLEANCONFDIR"
  sed -ir 's/^[[:space:]]*obsoleted_option([[:space:]]|$)/new_option /' \
    > "$dst_foo_conf"
  {
    #FIXME !!!
    echo -n "The \"obsoleted_option\" in the $foo_conf file has been renamed"
    echo -n " on new system to \"new_option\". This has been fixed"
    echo -n " and fixed configuration file will be applied on new system"
    echo    " automatically."
    echo
  } >> "$SOLUTION_FILE"
  set_result $RESULT_FIXED
fi

# case 2)
if grep -q "deprecated_option" "$foo_conf"; then
  log_medium_risk "The 'deprecated_option' is used inside '$foo_conf'."

  if [ -e "$dst_foo_conf" ]; then
    || cp -ar "$foo_conf" "$PREUPG_CLEANCONFDIR"
  sed -ir 's/^[[:space:]]*deprecated_option([[:space:]]|$)/#deprecated_option /' \
    > "$dst_foo_conf"
  {
    #FIXME !!!
    echo -n "The \"deprecated_option\" option has been removed on new system."
    echo -n " You should check correct functionality of your applications."
    echo -n " The option has been commented out."
    echo
  } >> "$SOLUTION_FILE"
  set_result $RESULT_FAIL
fi

# case 3
# ok, we will pretend, that when naughty-foo-cottage subpackage is installed,
# we will want to install naughty-foo-house on new system
if is_pkg_installed "naughty-foo-house"; then
  log_info "The package naughty-foo-cottage has been split on new system. naughty-foo-house will be installed."
  echo -n "The package naughty-foo-cottage has been split on new system and part"
  echo -n " of current funcionality is provided by the naughty-foo-house package."
  echo    " The new package will be installed automatically by post-upgrade script."
  echo
  cp -a "$post_script" "$POSTUPGRADE_DIR"
  chmod +x "${POSTUPGRADE_DIR}/${post_script}"
  set_result $RESULT_FIXED
fi


#
# Use expected exit code to provide info about result of the script.
#
exit $ret

