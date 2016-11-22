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
#   In case a manual inspection, check or action BEFORE the upgrade is needed,
#   do the following things:
#     1) provide a text in $SOLUTION_FILE: a description of the problem and remediation instructions
#     2) use "log_high_risk" to provide a short message that a problem was found
#     3) exit by "exit_failed" to inform preupg, that something unusual happened
#           - or: exit $RESULT_FAILED
#

# So now you know that the foo RPM package is installed (because you set 'foo' in the "applies_to" option
# in the content.ini file). In this example, if the $foo_conf file exists and if it
# contains an "explode_on_new_system" substring, you are informed that an action is required before the upgrade:
foo_conf="/etc/preupg-foo-example"
if [[ -e "$foo_conf" ]] && grep -q "explode_on_new_system" "$foo_conf"; then
  log_high_risk "Found a dangerous option in $foo_conf."
  {
    echo -n "The $foo_conf config file of the foo package contains a dangerous option"
    echo -n " 'explode_on_new_system', which will blow up your machine when"
    echo -n " you keep it. Remove the option from the file before"
    echo    " the upgrade to prevent your machine from exploding."
  } >> "$SOLUTION_FILE"

  exit_failed
fi

#
# Again, when there is not an issue anymore, exit by "exit_pass".
#
exit_pass
