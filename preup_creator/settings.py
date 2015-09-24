temp_check_script = """#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

### For more information see 'man preupg-content-creator' or 'man preupgrade-assistant-api'.

"""

group_name = 'Specify a group name which content belongs to (like database):'
content_name = 'Specify a module name which will be created (like mysql):'
check_script = "Specify a script name which will be used for assessment:"
solution_text = "Specify a solution file which will be shown in report:"
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
