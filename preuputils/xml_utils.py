from __future__ import print_function, unicode_literals

import re
import os
import six

from preup.xml_manager import html_escape_string
from preup.utils import get_assessment_version, get_file_content, write_to_file
from preup.utils import print_error_msg
from preup import settings
from preuputils import xml_tags
from preuputils import script_utils


def get_full_xml_tag(dirname):
    """We need just from RHEL directory"""
    found = 0
    # Get index of scenario and cut directory till scenario (included)
    for index, dir_name in enumerate(dirname.split(os.path.sep)):
        if re.match(r'\D+(\d)_(\D*)(\d)-results', dir_name, re.I):
            found = index
    main_dir = dirname.split(os.path.sep)[found+1:]
    return main_dir


class XmlUtils(object):
    """Class generate a XML from xml_tags and loaded INI file"""
    def __init__(self, dir_name, ini_files):
        self.keys = {}
        self.select_rules = []
        self.rule = []
        self.dirname = dir_name
        self.ini_files = ini_files

    def update_files(self, file_name, content):
        """Function updates file_name <migrate or update> according to INI file."""

        """
        :param file_name: specified in INI file like mode: upgrade, migrate
        :param content: name of the content like xccdf_rule_...
        :return: Nothing
        """
        path_name = os.path.join(settings.UPGRADE_PATH, file_name)
        lines = []
        if os.path.exists(path_name):
            lines = get_file_content(path_name, 'rb', method=True)
        test_content = [x.strip() for x in lines if content in x.strip()]
        if not test_content:
            lines.append(content + '\n')
            write_to_file(path_name, 'wb', lines)

    def _update_check_description(self, filename):
        new_text = []
        lines = get_file_content(os.patch.join(self.dirname, filename), "rb", True)

        bold = '<xhtml:b>{0}</xhtml:b>'
        br = '<xhtml:br/>'
        table_begin = '<xhtml:table>'
        table_end = '</xhtml:table>'
        table_header = '<xhtml:tr><xhtml:th>Result</xhtml:th><xhtml:th>Description</xhtml:th></xhtml:tr>'
        table_row = '<xhtml:tr><xhtml:td>{0}</xhtml:td><xhtml:td>{1}</xhtml:td></xhtml:tr>'
        new_text.append(br + br + '\n' + bold.format('Details:') + br)
        results = False
        for index, line in enumerate(lines):
            if '=' in line:
                if not results:
                    new_text.append(bold.format('Expected results:') + br)
                    new_text.append(table_begin + '\n' + table_header)
                    results = True
                try:
                    exp_results = line.strip().split('=')
                    new_text.append(table_row.format(exp_results[0], exp_results[1]) + '\n')
                except IndexError:
                    pass
            else:
                new_text.append(line.rstrip() + br)
        if results:
            new_text.append(table_end + '\n')

        return '\n'.join(new_text)

    def update_values_list(self, section, search_exp, replace_exp):
        """
        The function replaces tags taken from INI files.
        Tags are mentioned in xml_tags.py
        """
        forbidden_empty = ["{scap_name}", "{main_dir}"]
        if search_exp == "{content_description}":
            replace_exp = replace_exp.rstrip()
        elif search_exp == "{check_description}":
            replace_exp = '\n' + replace_exp + '\n'
        elif search_exp == "{config_file}":
            new_text = ""
            for lines in replace_exp.split(','):
                new_text = new_text+"<xhtml:li>"+lines.strip()+"</xhtml:li>"
            replace_exp = new_text.rstrip()
        elif search_exp == "{solution}":
            new_text = get_file_content(os.path.join(self.dirname, replace_exp), "rb", True)
            # we does not need interpreter for fix script
            # in XML therefore skip first line
            replace_exp = ''.join(new_text[1:])
        elif search_exp == "{solution_text}":
            new_text = "_" + '_'.join(get_full_xml_tag(self.dirname))\
                       + "_SOLUTION_MSG_" + replace_exp.upper()
            replace_exp = new_text
        if replace_exp == '' and search_exp in forbidden_empty:
            print_error_msg(title="Disapproved empty replacement for tag '%s'" % search_exp)
            os.sys.exit(1)

        for cnt, line in enumerate(section):
            if search_exp in line:
                section[cnt] = line.replace(search_exp, replace_exp)

    def check_recommended_fields(self, keys=None, script_name=""):
        """
        The function checks whether all fields in INI file are fullfiled
        If solution_type is mentioned than HTML page can be used.
        HTML solution type can contain standard HTML tags

        field are needed by YAML file
        """
        fields = ['content_title', 'check_script', 'solution', 'applies_to']
        optional = ['solution_type']
        unused = [x for x in fields if not keys.get(x)]
        if unused:
            title = 'Following tags are missing in INI file %s\n' % script_name
            if 'applies_to' not in unused:
                print_error_msg(title=title, msg=unused)
                os.sys.exit(1)
        if 'solution_type' in keys:
            if keys.get('solution_type') == "html" or keys.get('solution_type') == "text":
                pass
            else:
                print_error_msg(
                    title="Wrong solution_type. Allowed are 'html' or 'text' %s" % script_name
                )
                os.sys.exit(0)

    def add_value_tag(self):
        """The function adds VALUE tag in group.xml file"""
        value_tag = []
        check_export_tag = list()
        check_export_tag.append(xml_tags.RULE_SECTION_VALUE_IMPORT)
        for key, val in xml_tags.DIC_VALUES.items():
            value_tag.append(xml_tags.VALUE)
            if key == 'current_directory':
                val = '/'.join(get_full_xml_tag(self.dirname))
                val = 'SCENARIO/' + val
            self.update_values_list(value_tag, "{value_name}", val)
            self.update_values_list(value_tag, "{val}", key.lower())
            check_export_tag.append(xml_tags.RULE_SECTION_VALUE)
            self.update_values_list(check_export_tag, "{value_name_upper}", key.upper())
            self.update_values_list(check_export_tag, "{val}", key.lower())
        return value_tag, check_export_tag

    def solution_modification(self, key):
        """Function handles a solution text or scripts"""
        fix_tag = []
        for k in key['solution'].split(','):
            k = k.strip()
            script_utils.check_scripts('solution', self.dirname, script_name=k)
            script_type = script_utils.get_script_type(self.dirname, script_name=k)
            if script_type == "txt":
                fix_tag.append(xml_tags.FIX_TEXT)
            else:
                fix_tag.append(xml_tags.FIX)

            self.update_values_list(fix_tag, "{solution_text}",
                                    key['solution_type'] if 'solution_type' in key else "text")
            self.update_values_list(fix_tag, "{solution}", k)
            self.update_values_list(fix_tag, "{script_type}", script_type)
        self.update_values_list(self.rule, '{fix}', ''.join(fix_tag))

    def check_script_modification(self, key, k):
        """Function checks a check script"""
        script_utils.check_scripts(k, self.dirname, script_name=key[k])
        check_func = {'log_': ['log_none_risk', 'log_slight_risk',
                               'log_medium_risk', 'log_high_risk',
                               'log_extreme_risk', 'log_info',
                               'log_error', 'log_warning'],
                      'exit_': ['exit_error', 'exit_fail',
                                'exit_fixed', 'exit_not_applicable',
                                'exit_pass', 'exit_unknown',
                                'exit_informational']}
        for check in check_func:
            script_utils.check_inplace_risk(self.dirname,
                                            prefix=check,
                                            script_name=key[k],
                                            check_func=check_func[check])
        self.update_values_list(self.rule, "{scap_name}", key[k].split('.')[0])
        requirements = {'applies_to': 'check_applies',
                        'binary_req': 'check_bin',
                        'requires': 'check_rpm'}
        updates = dict()
        for req in requirements:
            if req in key:
                updates[requirements[req]] = key[req]
        script_utils.update_check_script(self.dirname,
                                         updates,
                                         script_name=key[k],
                                         author=key['author'] if 'author' in key else "")
        self.update_values_list(self.rule, "{"+k+"}", key[k])

    def prepare_sections(self):
        """The function prepares all tags needed for generation group.xml file."""
        group_ini = False
        for main, self.keys in self.ini_files.items():
            if main.endswith("group.ini"):
                self.rule.append(xml_tags.GROUP_INI)
                for k in self.keys:
                    self.update_values_list(self.rule, '{group_title}', k['group_title'])
                    self.update_values_list(self.rule, '{group_value}', "")
            else:
                self.rule.append(xml_tags.CONTENT_INI)
                self.create_xml_from_ini(main)
                self.update_values_list(self.rule,
                                        "{select_rules}",
                                        ' '.join(self.select_rules))
            xml_tag = "{main_dir}"
            self.update_values_list(self.rule,
                                    xml_tag,
                                    '_'.join(get_full_xml_tag(self.dirname)))
        return self.rule

    def fnc_config_file(self, key, name):
        """Function updates a config file."""
        if name in key and key[name] is not None:
            self.update_values_list(self.rule, "{config_section}",
                                    xml_tags.CONFIG_SECTION)
            self.update_values_list(self.rule, "{config_file}",
                                    key['config_file'])
        else:
            self.update_values_list(self.rule, "{config_section}", "")

    def fnc_check_script(self, key, name):
        """ Function updates a check_script """
        if name in key:
            self.check_script_modification(key, name)
            self.update_values_list(self.select_rules, "{scap_name}",
                                    key[name].split('.')[0])

    def fnc_check_description(self, key, name):
        """ Function updates a check_description """
        if name in key and key[name] is not None:
            escaped_text = self._update_check_description(key[name])
            self.update_values_list(self.rule, "{check_description}", escaped_text)
        else:
            self.update_values_list(self.rule, "{check_description}", "")

    def fnc_solution_text(self, key, name):
        """Function updates a solution text."""
        if name in key:
            self.solution_modification(key)
        else:
            self.update_values_list(self.rule, "{fix}", xml_tags.FIX_TEXT)
            self.update_values_list(self.rule, "{solution_text}", "text")
            self.update_values_list(self.rule, "{platform_id}",
                                    get_assessment_version(self.dirname)[1])

    def fnc_update_mode(self, key, name):

        """
        Function update <upgrade_path>/<migrate.conf|update.conf> files
        migrate_xccdf_path
        :param key:
        :param name:
        :return:
        """

        content = "{rule}{main_dir}_{name}".format(rule=xml_tags.TAG_RULE,
                                                   main_dir='_'.join(get_full_xml_tag(self.dirname)),
                                                   name=key.split('.')[0])
        if not name:
            self.update_files('migrate', content)
            self.update_files('upgrade', content)
        for x in name.split(','):
            self.update_files(x.strip(), content)

    def dummy_fnc(self, key, name):
        """Function is only dummy."""
        pass

    def update_text(self, key, name):
        """Function updates a text."""
        if key[name] is not None:
            # escape values so they can be loaded as XMLs
            escaped_text = html_escape_string(key[name])
            self.update_values_list(self.rule, "{"+name+"}", escaped_text)

    def create_xml_from_ini(self, main):
        """
        The function creates group.xml file from INI file.
        All tag are replaced by function update_value_list

        Function also checks whether check script full fills all criteria
        """
        self.select_rules.append(xml_tags.SELECT_TAG)
        update_fnc = {
            'config_file': self.fnc_config_file,
            'check_script': self.fnc_check_script,
            'check_description': self.fnc_check_description,
            'solution': self.fnc_solution_text,
            'applies_to': self.dummy_fnc,
            'binary_req': self.dummy_fnc,
            'content_title': self.update_text,
            'content_description': self.update_text,
        }
        for key in self.keys:
            self.check_recommended_fields(key, script_name=main)
            # Add solution text into value
            if 'solution' in key:
                xml_tags.DIC_VALUES['solution_file'] = key['solution']
            else:
                xml_tags.DIC_VALUES['solution_file'] = 'solution.txt'

            # Add flag where will be shown content if in admin part or in user part
            if 'result_part' in key:
                xml_tags.DIC_VALUES['result_part'] = key['result_part']
            else:
                xml_tags.DIC_VALUES['result_part'] = 'admin'

            self.update_values_list(self.rule, "{rule_tag}",
                                    ''.join(xml_tags.RULE_SECTION))
            value_tag, check_export_tag = self.add_value_tag()
            self.update_values_list(self.rule, "{check_export}",
                                    ''.join(check_export_tag))
            self.update_values_list(self.rule, "{group_value}",
                                    ''.join(value_tag))

            for k, function in six.iteritems(update_fnc):
                try:
                    function(key, k)
                except IOError as e:
                    e_title = "Wrong value for tag '%s' in INI file '%s'\n" % (k, main)
                    e_msg = "'%s': %s" % (key[k], e.strerror)
                    print_error_msg(title=e_title, msg=e_msg)
                    os.sys.exit(1)

            self.update_values_list(self.rule, '{group_title}', html_escape_string(key['content_title']))
            try:
                if 'mode' not in key:
                    self.fnc_update_mode(key['check_script'], 'migrate, upgrade')
                else:
                    self.fnc_update_mode(key['check_script'], key['mode'])
            except KeyError:
                pass
