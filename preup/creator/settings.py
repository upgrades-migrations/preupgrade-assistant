temp_check_script = """#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.

"""

default_group = 'system'
default_module = 'packages'
default_script_name = 'check.sh'
default_solution_name = 'solution.txt'
group_name = 'Specify a group name which content belongs to [%s]:' % default_group
content_name = 'Specify a module name which will be created [%s]:' % default_module
check_script = "Specify a script name which will be used for assessment: [%s]" % default_script_name
solution_text = "Specify a solution file which will be shown in report: [%s]" % default_solution_name
content_title = "Specify a content title:"
content_desc = "Would you like to specify a content description?"
content_desc_text = "Write down a content description:"
upgrade_path = "Specify a upgrade path (like RHEL6_7) where a content will be stored:"
summary_title = 'preupg-content-creator generates these files which should be updated:'
summary_directory = '- content was created in directory %s.'
summary_ini = '- ini file which defines a content is %s.'
summary_check = '- check script which does an assessment is %s. Update it before an usage'
summary_solution = '- solution text which informs about incompatilibies is %s. Update it before an usage'
check_path = "File %s already exists. Do you want to replace the file?"

text_for_testing = "\nFor testing content run these two commands:\n" \
                   "- preupg-create-group-xml %s to create XML file\n" \
                   "- preupg -c %s"