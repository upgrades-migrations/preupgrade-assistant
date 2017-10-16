temp_bash_script = """#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.

"""

temp_python_script = """#!/usr/bin/python
# -*- Mode: Python; python-indent: 8; indent-tabs-mode: t -*-

import sys
import os

from preupg.script_api import *

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.
"""
default_group = 'system'
default_module = 'packages'
group_name = 'Specify the group name which the module belongs to [%s]:' % default_group
content_name = 'Specify the module name which will be created [%s]:' % default_module
content_title = "Specify the module title:"
content_desc_text = "Specify the module description:"
upgrade_path = "Specify the name of the module set directory in which the module will be created:"
summary_title = 'preupg-content-creator generated these files to be updated:'
summary_directory = '- the module was created in the %s directory.'
summary_ini = '- the INI file which defines the module is %s.'
summary_check = '- the check script which provides an assessment is %s. Update it before you use it.'
summary_solution = '- the solution text which informs about incompatibilities %s. Update it before you use it.'
check_path = "The %s file already exists. Do you want to replace the file?"
type_check_script = "Would you like to create a BASH or Python check script? [sh/py] Bash is default."
prop_src_version = "Specify major source OS version e.g. \"6\":"
prop_dst_version = "Specify major destination OS version e.g. \"7\":"
commands_to_use_new_module = "\nTo use the newly created module with the" \
                             " Preupgrade Assistant run these commands:\n" \
                             "- preupg-xccdf-compose %s\n" \
                             "- preupg -c %s"
