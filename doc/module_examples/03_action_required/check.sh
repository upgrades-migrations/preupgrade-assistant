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
#   In case we want to manual action/check BEFORE UPGRADE by user,
#   we have to do basically just 3 things:
#     1) provide text in $SOLUTION_FILE - what is the problem, instructions,...
#     2) use log_high_risk to provide short message that we found problem
#     3) exit by exit_failed - to inform preupg, that something happend
#           - or: exit $RESULT_FAILED
##

#
# So now we know that rpm foo is installed (we set 'foo' for applies_to option
# in content.ini file). In this example, when file $foo_conf exists and
# contains substring "explode_on_new_system", we inform user that action
# before upgrade is required.
#
foo_conf="/etc/preupg-foo-example"
if [[ -e "$foo_conf" ]] && grep -q "explode_on_new_system" "$foo_conf"; then
  log_risk_risk "Found dangerous option in $foo_conf."
  {
    echo -n "The $foo_conf config file of foo tool contains dangerous option"
    echo -n " 'explode_on_new_system', which will blow up your mahine when"
    echo -n " you keep it. You have to remove the option from the file before"
    echo    " upgrade to prevent your machine against explosion."
  } >> "$SOLUTION_FILE"

  exit_failed
fi

#
# At the end, when issue isn't presented, we will we want to
# inform user, that everything is OK and we did some check. For this case
# we will exit by exit_pass.
#
# NOTE: you should know, that content of $SOLUTION_FILE will not be printed
#       the report, because doesn't make sense and we don't want to produce
#       a lot of text when it is not necessary. So you don't need truncate
#       the file, even when you printed there some text.
exit_pass
