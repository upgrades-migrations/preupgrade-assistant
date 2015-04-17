from __future__ import print_function

import sys
import os
import re
import mimetypes

from contextlib import closing
from preup.utils import get_file_content, write_to_file, print_error_msg
from preup import settings


def get_full_path(dir_name, script_name):
    """
    The function returns full path
    """
    return os.path.join(dir_name, script_name)


def check_scripts(type_name, dir_name, script_name=None):
    """
    The function checks whether script exists in content directory
    If check_script exists then the script checks whether it is executable
    """
    if not os.path.exists(get_full_path(dir_name, script_name)):
        print ("ERROR: ", dir_name, script_name, "Script name does not exists")
        print ("List of directory (", dir_name, ") is:")
        for file_name in os.listdir(dir_name):
            print (file_name)
        sys.exit(1)
    if type_name != 'solution':
        check_executable(dir_name, script_name)


def apply_function(updates, begin_fnc, end_fnc, sep, script_type):
    """
    The function generates check_applies_to function into check_scripts
    mentioned in BASH or Python
    """
    template = 'check_applies_to ' + begin_fnc
    if script_type == "sh":
        template += '"' + updates['check_applies'] + '"'
    else:
        template += 'check_applies="' + updates['check_applies'] + '"'
    template += end_fnc
    return template


def rpm_bin_function(updates, begin_fnc, end_fnc, sep, script_type):
    """
    The function generates check_rpm_to function into check_scripts
    mentioned in BASH or Python
    """
    if script_type == "python":
        fnc_name = ['check_rpm="', 'check_bin="']
    else:
        fnc_name = ['"', '"']
    template = 'check_rpm_to ' + begin_fnc + fnc_name[0]

    if "check_rpm" in updates and updates['check_rpm'] is not None:
        template += updates['check_rpm'] + '"'
    else:
        template += '"'
    template += sep + fnc_name[1]
    if "check_bin" in updates and updates['check_bin'] is not None:
        template += updates['check_bin'] + '"'
    else:
        template += '"'
    template += end_fnc

    return template


def generate_common_stuff(lic, updates, script_type):
    """
    Function generates a common stuff
    for Python and BASH scripts
    """
    generated_section = []
    functions = ['check_applies_to', 'check_rpm_to', 'switch_to_content']
    pre_comment = ""
    begin_fnc = ""
    end_fnc = ""
    sep = " "
    if script_type == "sh":
        pre_comment = '#'
    else:
        lic = '"""'+lic+'"""'
        begin_fnc = "("
        end_fnc = ")"
        sep = ","
    if settings.autocomplete:
        for row_lic in lic.split('\n'):
            functions.append(pre_comment + row_lic)
            generated_section.append(pre_comment + row_lic)
    if script_type == "sh":
        functions.append('/usr/share/preupgrade/common.sh')
        generated_section.append('. /usr/share/preupgrade/common.sh')
    if "check_applies" in updates:
        generated_section.append(
            apply_function(updates, begin_fnc, end_fnc, sep, script_type)
        )
    if "check_bin" in updates or "check_rpm" in updates:
        generated_section.append(
            rpm_bin_function(updates, begin_fnc, end_fnc, sep, script_type)
        )
    return generated_section, functions


def update_check_script(dir_name, updates, script_name=None, author=""):
    """
    The function updates check script with license file
    and with API functions like check_rpm_to and check_applies_to
    """
    script_type = get_script_type(dir_name, script_name)
    if author == "":
        author = "<empty_line>"
    generated_section, functions = generate_common_stuff(settings.license.format(author),
                                                         updates,
                                                         script_type)
    full_path_script = get_full_path(dir_name, script_name)
    lines = get_file_content(full_path_script, "r", method=True)
    if not [x for x in lines if re.search(r'#END GENERATED SECTION', x)]:
        print_error_msg("#END GENERATED SECTION is missing in check_script {0}".
                                  format(full_path_script))
    for func in functions:
        lines = [x for x in lines if func not in x.strip()]
    output_text = ""
    for line in lines:
        if '#END GENERATED SECTION' in line:
            new_line = '\n'.join(generated_section)
            new_line = new_line.replace('<empty_line>', '').replace('<new_line>', '')
            output_text += new_line+'\n'
            if 'check_applies' in updates:
                component = updates['check_applies']
            else:
                component = "distribution"
            if script_type == "sh":
                output_text += 'COMPONENT="'+component+'"\n'
            else:
                output_text += 'set_component("'+component+'")\n'
        output_text += line
    write_to_file(full_path_script, "w", output_text)


def check_executable(dir_name, script_name=""):
    """
    The function checks whether script is executable.
    If not then ERROR message arise
    """
    if not os.access(get_full_path(dir_name, script_name), os.X_OK):
        print_error_msg(title="The file %s is not executable" % os.path.join(dir_name, script_name))


def get_script_type(dir_name, script_name=""):
    """
    The function returns type of check_script.
    If it's not any script then return just txt
    """
    mime_type = mimetypes.guess_type(get_full_path(dir_name, script_name))[0]
    file_types = {'text/x-python': 'python',
                  'application/x-csh': 'csh',
                  'application/x-sh': 'sh',
                  'application/x-perl': 'perl',
                  'text/plain': 'txt',
                  'None': 'txt',
                  }
    return file_types[mime_type]


def check_inplace_risk(dir_name, prefix="", script_name="", check_func=[]):
    """
    The function checks inplace risks
    in check_script and informs user in case of wrong usage
    """
    lines = get_file_content(get_full_path(dir_name, script_name), "r")
    compile_req = re.compile(r'^#', re.M|re.I)
    lines = [x for x in lines if not compile_req.search(x.strip())]
    inplace_lines = [x for x in lines if prefix in x]
    for line in inplace_lines:
        tags = [x for x in check_func if re.findall('\\b'+x.split()[0]+'\\b', line)]
        if not tags:
            continue
        checks = [x for x in check_func if len(x.split()) > 1]
        tags = [x for x in checks if re.findall('\\b'+x.split()[1]+'\\b', line)]
        if not tags:
            continue
