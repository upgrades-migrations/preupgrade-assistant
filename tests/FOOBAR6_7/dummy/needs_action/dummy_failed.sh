#!/bin/bash

echo "Dummy needs_action test"

echo "preupg.risk.HIGH: This is High Risk"

. /usr/share/preupgrade/common.sh
#END GENERATED SECTION

exit $XCCDF_RESULT_FAIL
