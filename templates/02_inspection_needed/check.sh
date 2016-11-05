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
#   In case we want to manual inspection/check/action AFTER UPGRADE by user,
#   we have to do basically just 3 things:
#     1) provide text in $SOLUTION_FILE - what is the problem, instructions,...
#     2) use log_medium_risk to provide short message that we found problem
#     3) exit by exit_failed - to inform preupg, that something happend
#           - or: exit $RESULT_FAILED
##

#
# So now we know that rpm foo is installed (we set 'foo' for applies_to option
# in content.ini file). In this example, when file $foo_conf exists and
# contains 'deprecated_option', we inform user about found issue
#
foo_conf="/etc/preupg-foo-example"
if [[ -e "$foo_conf" ]] && grep -q "^deprecated_option" "$foo_conf"; then
  log_medium_risk "Found deprecated option in $foo_conf"
  {
    echo -n "The $foo_conf config file of foo tool contains deprecated option"
    echo -n " 'deprecated_option' which is not available on new system. This"
    echo -n " may affect functionality of your other applications, which"
    echo -n " depend on it."
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
