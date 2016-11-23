#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

#
# The whole section above is processed and modified by the preupg-xccdf-compose
# script, according to the contents of the INI file (in this case it is the content.ini file).
# In addition, the LICENSE used by the Preupgrade Assistant is inserted.
#

##
# Briefly:
#   In case a manual inspection, check or action AFTER the upgrade is needed,
#   do the following things:
#     1) provide a text in $SOLUTION_FILE: a description of the problem and remediation instructions
#     2) use "log_medium_risk" to provide a short message that a problem was found
#     3) exit by "exit_failed" to inform preupg, that something unusual happened
#           - or: exit $RESULT_FAILED
##

#
# So now you know that the foo RPM package is installed (because you set 'foo' in the "applies_to" option
# in the content.ini file). In this example, if the $foo_conf file exists and if it
# contains a deprecated 'CookieLogs' option, you are informed about the detected issue:
#
foo_conf="/etc/preupg-foo-example"
if [[ -e "$foo_conf" ]] && grep -q "^CookieLogs" "$foo_conf"; then
  log_medium_risk "Found a deprecated 'CookieLogs' option in $foo_conf"
  {
    echo -n "The $foo_conf config file in the foo package contains a deprecated option"
    echo -n " 'CookieLogs' which is not available on the new system. This"
    echo -n " might affect the functionality of the applications that"
    echo    " depend on the aforementioned option."
  } >> "$SOLUTION_FILE"

  exit_failed
fi

#
# In the end, when the issue is resolved, you want to be informed that the check has been done and
# everything is OK now. In this case, exit the module
# by "exit_pass".
#
# Reminder: when you use "exit_pass", the content of the solution file is ignored and not printed.
#
exit_pass
