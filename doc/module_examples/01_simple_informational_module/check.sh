#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

#
# The whole section above is processed and modified by preupg-xccdf-compose
# script, according to content of INI file (in this case content.ini).
# And in addition the LICENSE used by PreupgradeAssistant is inserted.
#

#
# Log short informational message, which inform user briefly about just
# something what could be interesting but doesn't generate any risk for
# upgrade to new system
#

log_info "You run your first module! Congratulation. See report for more information."

#
# Usually there are cases when you want to add some another information
# to the solution file. For example, we will check, whether you have installed
# preupgrade-assistant package or you use definitelly just upstream source
# code.
#
if is_pkg_installed "preupgrade-assistant"; then
  log_info "You have installed the preupgrade-assistant package!"
  {
    echo
    echo    "You should know, that preupgrade-assistant has upstream here:"
    echo    "  https://github.com/upgrades-migrations/preupgrade-assistant"
    echo
    echo -n "You can monitor up-to-date upstream version for further"
    echo    " development. Also you can report issues here or on the site:"
    echo    " http://bugzilla.redhat.com/"
  } >> "$SOLUTION_FILE"
else
  log_info "You run upstream version of preupgrade-assistant probably. Great to see it :-)"
fi

#
# IMPORTANT: 
#  The script has to ends with specific exit code, which says, type of result,
#  In this case, we want to just informational result. See common.sh
exit_informational
