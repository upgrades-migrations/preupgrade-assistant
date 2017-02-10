from __future__ import print_function, unicode_literals

import re
import os
import six
import sys
import copy

from preupg.xml_manager import html_escape_string
from preupg.utils import SystemIdentification, FileHelper
from preupg import settings
from preupg.xmlgen import xml_tags
from preupg.xmlgen.script_utils import ModuleHelper
from preupg.exception import MissingTagsIniFileError, EmptyTagGroupXMLError


def get_full_xml_tag(dirname):
    """We need just from RHEL directory"""
    found = 0
    # Get index of scenario and cut directory till scenario (included)
    for index, dir_name in enumerate(dirname.split(os.path.sep)):
        if re.match(r'\D+(\d)_(\D*)(\d)-results', dir_name, re.I):
            found = index
    main_dir = dirname.split(os.path.sep)[found + 1:]
    return main_dir


class XmlUtils(object):
    """Class generate a XML from xml_tags and loaded INI file"""
    def __init__(self, dir_name, ini_files):
        self.keys = {}
        self.select_rules = []
        self.rule = []
        self.dirname = dir_name
        self.ini_files = ini_files
        self._test_init_file()
        self.mh = None

    def _test_init_file(self):
        test_dict = copy.deepcopy(self.ini_files)
        allowed_tags = ['check_script', 'content_description', 'content_title', 'applies_to',
                        'author', 'binary_req', 'solution', 'bugzilla', 'config_file',
                        'group_title', 'mode', 'requires', 'solution_type']
        for ini, content in six.iteritems(test_dict):
            content_dict = content[0]
            for tag in allowed_tags:
                if tag in content_dict:
                    del content_dict[tag]
            if content_dict:
                tags = ','. join(six.iterkeys(content_dict))
                sys.stderr.write("Warning: The tag(s) '%s' not allowed in INI"
                                 " file %s.\nAllowed tags are %s.\n"
                                 % (tags, ini, ', '.join(allowed_tags)))

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
            lines = FileHelper.get_file_content(path_name, 'rb', method=True)
        test_content = [x.strip() for x in lines if content in x.strip()]
        if not test_content:
            lines.append(content + '\n')
            FileHelper.write_to_file(path_name, 'wb', lines)

    def _update_check_description(self, filename):
        new_text = []
        lines = FileHelper.get_file_content(os.path.join(self.dirname, filename), "rb", True)

        bold = '<xhtml:b>{0}</xhtml:b>'
        br = '<xhtml:br/>'
        table_begin = '<xhtml:table>'
        table_end = '</xhtml:table>'
        table_header = '<xhtml:tr><xhtml:th>Result</xhtml:th><xhtml:th>Description</xhtml:th></xhtml:tr>'
        table_row = '<xhtml:tr><xhtml:td>{0}</xhtml:td><xhtml:td>{1}</xhtml:td></xhtml:tr>'
        new_text.append(br + br + '\n' + bold.format('Details:') + br)
        results = False
        for line in lines:
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
            new_text = FileHelper.get_file_content(os.path.join(self.dirname, replace_exp), "rb", True)
            # we does not need interpreter for fix script
            # in XML therefore skip first line
            replace_exp = ''.join(new_text[1:])
        elif search_exp == "{solution_text}":
            new_text = "_" + '_'.join(get_full_xml_tag(self.dirname))\
                       + "_SOLUTION_MSG_" + replace_exp.upper()
            replace_exp = new_text
        if replace_exp == '' and search_exp in forbidden_empty:
            raise EmptyTagGroupXMLError(search_exp)

        for cnt, line in enumerate(section):
            if search_exp in line:
                section[cnt] = line.replace(search_exp, replace_exp)

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
            if key == 'module_path':
                val = '_'.join(get_full_xml_tag(self.dirname))
            self.update_values_list(value_tag, "{value_name}", val)
            self.update_values_list(value_tag, "{val}", key.lower())
            check_export_tag.append(xml_tags.RULE_SECTION_VALUE)
            self.update_values_list(check_export_tag, "{value_name_upper}", key.upper())
            self.update_values_list(check_export_tag, "{val}", key.lower())
        for key, val in xml_tags.GLOBAL_DIC_VALUES.items():
            check_export_tag.append(xml_tags.RULE_SECTION_VALUE_GLOBAL)
            self.update_values_list(check_export_tag, "{value_name_upper}", key.upper())
            self.update_values_list(check_export_tag, "{value_name}", key)

        return value_tag, check_export_tag

    def solution_modification(self, key):
        """Function handles a solution text or scripts"""
        fix_tag = []
        for k in key['solution'].split(','):
            self.mh.check_scripts('solution')
            script_type = FileHelper.get_script_type(self.mh.get_full_path_name_solution())
            if script_type == "txt":
                fix_tag.append(xml_tags.FIX_TEXT)
            else:
                fix_tag.append(xml_tags.FIX)
            if 'solution_type' in key:
                solution_type = key['solution_type']
            else:
                solution_type = "text"
            self.update_values_list(fix_tag, "{solution_text}", solution_type)
            self.update_values_list(fix_tag, "{solution}", k.strip())
            self.update_values_list(fix_tag, "{script_type}", script_type)
        self.update_values_list(self.rule, '{fix}', ''.join(fix_tag))

    def check_script_modification(self, key, k):
        """Function checks a check script"""
        self.mh.check_scripts(k)
        check_func = {'log_': ['log_slight_risk',
                               'log_medium_risk', 'log_high_risk',
                               'log_extreme_risk', 'log_info',
                               'log_error', 'log_warning'],
                      'exit_': ['exit_error', 'exit_fail',
                                'exit_fixed', 'exit_not_applicable',
                                'exit_pass', 'exit_informational']
                      }
        for check in check_func:
            self.mh.check_inplace_risk(prefix=check, check_func=check_func[check])
        self.update_values_list(self.rule, "{scap_name}", key[k].split('.')[0])
        requirements = {'applies_to': 'check_applies',
                        'binary_req': 'check_bin',
                        'requires': 'check_rpm'}
        updates = dict()
        for req in requirements:
            if req in key:
                updates[requirements[req]] = key[req]
        if 'author' in key:
            author = key['author']
        else:
            author = None
        self.mh.update_check_script(updates, author=author)
        self.update_values_list(self.rule, "{"+k+"}", key[k])

    def prepare_sections(self):
        """The function prepares all tags needed for generation group.xml file."""
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
                                    SystemIdentification.get_assessment_version(self.dirname)[1])

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
            self.update_values_list(self.rule, "{" + name + "}", escaped_text)

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
            if 'check_script' not in key:
                raise MissingTagsIniFileError(tags="check_script", ini_file=main)
            if 'solution' not in key:
                raise MissingTagsIniFileError(tags="solution", ini_file=main)
            self.mh = ModuleHelper(os.path.dirname(main), key['check_script'], key['solution'])
            self.mh.check_recommended_fields(key, main)
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

            self.update_values_list(self.rule, "{rule_tag}", ''.join(xml_tags.RULE_SECTION))
            value_tag, check_export_tag = self.add_value_tag()
            self.update_values_list(self.rule, "{check_export}", ''.join(check_export_tag))
            self.update_values_list(self.rule, "{group_value}", ''.join(value_tag))

            for k, function in six.iteritems(update_fnc):
                try:
                    function(key, k)
                except IOError as e:
                    err_msg = "Invalid value of the field '%s' in INI file '%s'\n'%s': %s\n" \
                              % (k, main, key[k], e.strerror)
                    raise IOError(err_msg)

            self.update_values_list(self.rule, '{group_title}', html_escape_string(key['content_title']))
            try:
                if 'mode' not in key:
                    self.fnc_update_mode(key['check_script'], 'migrate, upgrade')
                else:
                    self.fnc_update_mode(key['check_script'], key['mode'])
            except KeyError:
                pass
