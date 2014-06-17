#!/bin/bash

echo "Dummy needs_action test"

echo "INPLACERISK: HIGH: This is High Risk"

. /usr/share/preupgrade/common.sh
COMPONENT="distribution"
#END GENERATED SECTION

exit $XCCDF_RESULT_FAIL
