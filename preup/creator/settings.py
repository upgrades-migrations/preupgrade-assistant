temp_bash_script = """#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.

"""

temp_python_script = """#!/usr/bin/python
# -*- Mode: Python; python-indent: 8; indent-tabs-mode: t -*-

import sys
import os

from preup.script_api import *

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.
"""
default_group = 'system'
default_module = 'packages'
default_bash_script_name = 'check.sh'
default_python_script_name = 'check.py'
default_solution_name = 'solution.txt'
group_name = 'Specify the group name which the module belongs to [%s]:' % default_group
content_name = 'Specify the module name which will be created [%s]:' % default_module
check_script = "Specify the script name which will be used for the assessment: [%s]"
solution_text = "Specify the solution file which will be shown in the report: [%s]" % default_solution_name
content_title = "Specify the module title:"
content_desc = "Would you like to specify the module description?"
content_desc_text = "Write the module description:"
upgrade_path = "Specify the upgrade path (like RHEL6_7) where the module will be stored:"
summary_title = 'preupg-content-creator generated these files to be updated:'
summary_directory = '- the module was created in the %s directory.'
summary_ini = '- the INI file which defines the module is %s.'
summary_check = '- the check script which provides an assessment is %s. Update it before you use it.'
summary_solution = '- the solution text which informs about incompatilibies is %s. Update it before you use it.'
check_path = "The %s file already exists. Do you want to replace the file?"
type_check_script = "Would you like to create a BASH or Python check script? [sh/py] Bash is default."

text_for_testing = "\nFor testing content run these two commands:\n" \
                   "- preupg-create-group-xml %s to create XML file\n" \
                   "- preupg -c %s"
