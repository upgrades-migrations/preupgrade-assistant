temp_check_script = """#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.

"""

default_group = 'system'
default_module = 'packages'
default_script_name = 'check.sh'
default_solution_name = 'solution.txt'
group_name = 'Specify the group name which the content belongs to [%s]:' % default_group
content_name = 'Specify the module name which will be created [%s]:' % default_module
check_script = "Specify the script name which will be used for the assessment: [%s]" % default_script_name
solution_text = "Specify the solution file which will be shown in the report: [%s]" % default_solution_name
content_title = "Specify the content title:"
content_desc = "Would you like to specify the content description?"
content_desc_text = "Write down the content description:"
upgrade_path = "Specify the upgrade path (like RHEL6_7) where the content will be stored:"
summary_title = 'preupg-content-creator generated these files to be updated:'
summary_directory = '- content was created in the %s directory.'
summary_ini = '- ini file which defines the content is %s.'
summary_check = '- check script which does the assessment is %s. Update it before using.'
summary_solution = '- solution text which informs about incompatilibies is %s. Update it before an usage'
check_path = "File %s already exists. Do you want to replace the file?"

text_for_testing = "\nFor testing content run these two commands:\n" \
                   "- preupg-create-group-xml %s to create XML file\n" \
                   "- preupg -c %s"
