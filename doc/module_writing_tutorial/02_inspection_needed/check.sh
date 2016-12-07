#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION


##
# Briefly:
#   This module script example is applicable for the scenario where any manual
#   action or inspection AFTER the upgrade is needed. The following is the
#   minimum such module should contain
#     1) provide a text in $SOLUTION_FILE: a description of the problem and
#        remediation instructions
#     2) use "log_medium_risk" to provide a short message that a problem was
#        found (Preupgrade Assistant requires the risk to be set to medium
#        in this scenario)
#     3) exit by "exit_failed" to inform preupg, that something unusual
#        happened
#           - or: "exit $RESULT_FAILED" which does the same as the above
##

#
# So now you know that the foo RPM package is installed (because you set 'foo'
# in the "applies_to" option in the module.ini file). In this example, if the
# $foo_conf file exists and if it contains a deprecated 'CookieLogs' option,
# you are informed about the detected issue:
#
foo_conf="/etc/preupg-foo-example"
if [[ -e "$foo_conf" ]] && grep -q "^CookieLogs" "$foo_conf"; then
  log_medium_risk "Found a deprecated 'CookieLogs' option in $foo_conf"
  {
    echo -n "The $foo_conf config file in the foo package contains a deprecated"
    echo -n " option 'CookieLogs' which is not available on the new system."
    echo -n " This might affect the functionality of the applications that"
    echo    " depend on the aforementioned option."
  } >> "$SOLUTION_FILE"

  exit_failed
fi

#
# In the end, when the issue is resolved, you want to be informed that the
# check has been done and everything is OK now. In this case, exit the module
# by "exit_pass".
#
# Reminder: when you use "exit_pass", the content of the solution file
# is ignored and not printed.
#
exit_pass
