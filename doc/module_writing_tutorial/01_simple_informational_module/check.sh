#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

#
# The whole section above is processed and modified by the preupg-xccdf-compose
# script, according to the contents of the INI file (in this case it is the
# content.ini file).
# In addition, the LICENSE used by the Preupgrade Assistant is inserted.
#

#
# Log a short informational message, which informs the user briefly about
# something that could be interesting, but does not generate any risks for the
# upgrade to a new system.
#

log_info "You are running your first module. Congratulations. See the report for more information."

#
# Usually there are cases when you want to add more information to the solution
# file. For example, you want to check if you have installed the
# preupgrade-assistant package or you are using the upstream source code.
#
if is_pkg_installed "preupgrade-assistant"; then
  log_info "You have installed the preupgrade-assistant package."
  {
    echo
    echo    "The preupgrade-assistant upstream can be found at:"
    echo    "  https://github.com/upgrades-migrations/preupgrade-assistant"
    echo
    echo -n "You can monitor the up-to-date upstream version for further"
    echo    " development. You can also report issues there or at:"
    echo    " http://bugzilla.redhat.com/"
  } >> "$SOLUTION_FILE"
else
  log_info "You are probably running an upstream version of the Preupgrade Assistant. Great to see it :-)"
fi

#
# IMPORTANT:
#  The script has to end with a specific exit code, which states a type of the
#  result. In this case, it is an informational result. See common.sh for
#  further information.
exit_informational
