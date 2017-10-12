from __future__ import print_function, unicode_literals

import os
import sys

from preupg.xml_manager import html_escape
from preupg.utils import FileHelper, ModuleSetUtils
from preupg import settings
from preupg.xmlgen import xml_tags
from preupg.xmlgen.script_utils import ModuleHelper
from preupg.exception import EmptyTagGroupXMLError


def module_path_from_root_dir(dirname, module_set_dir):
    """
    Remove module_set_dir from dirname path

    @param {str} dir_name - directory of specific module or module-set
        directory
    @param {str} module_set_dir - directory where all modules are stored

    @return {list} - splited path to module

    @example
    >>> module_path_from_root_dir(/root/RHEL6_7-results/selinux/CustomPolicy,
                                  /root/RHEL6_7-results)
    ['selinux', 'CustomPolicy']
    """
    return (dirname
            .replace(module_set_dir, '', 1)
            .lstrip(os.path.sep)  # remove first / from path
            .split(os.path.sep))


class XmlUtils(object):
    """Class generate a XML from xml_tags and loaded INI file"""
    def __init__(self, module_set_dir, module_dir, ini_files):
        """
        @param {str} module_set_dir - directory where all modules are stored
        @param {str} module_dir - directory of specific module or module-set
            directory
        @param {dict} ini_files - ini file options and their values in format:
            {ini_file_path: {option1: value, option2: value, ...}}
        """
        self.module_set_dir = module_set_dir
        self.module_dir = module_dir
        self.ini_files = ini_files
        self.select_rules = []
        self.rule = []
        self._test_config_file()
        self.mh = None

    def _test_config_file(self):
        """
        Checks if there are any illegal tags in config files i.e.
        (group.ini, module.ini) and print out warning message about them
        """
        allowed_tags = set(['content_description', 'content_title',
                            'applies_to', 'author', 'binary_req', 'bugzilla',
                            'config_file', 'group_title', 'mode', 'requires'])
        for ini_file, ini_content in iter(self.ini_files.items()):
            ini_content_tags = set(ini_content.keys())
            different = ini_content_tags.difference(allowed_tags)
            if different:
                sys.stderr.write("Warning: tags: '{0}' are not allowed "
                                 "in config file {1}.\n"
                                 "Allowed tags are {2}.\n"
                                 .format(', '
                                         .join(str(tag) for tag in different),
                                         ini_file,
                                         ', '.join(allowed_tags)))

    def update_files(self, file_name, content):
        """Function updates file_name <migrate or update> according to INI
        file.

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
        lines = FileHelper.get_file_content(os.path.join(self.module_dir,
                                                         filename), "rb", True)

        bold = '<xhtml:b>{0}</xhtml:b>'
        br = '<xhtml:br/>'
        table_begin = '<xhtml:table>'
        table_end = '</xhtml:table>'
        table_header = '<xhtml:tr><xhtml:th>Result</xhtml:th><xhtml:th>' \
                       'Description</xhtml:th></xhtml:tr>'
        table_row = '<xhtml:tr><xhtml:td>{0}</xhtml:td><xhtml:td>{1}' \
                    '</xhtml:td></xhtml:tr>'
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
                    new_text.append(table_row.format(exp_results[0],
                                                     exp_results[1]) + '\n')
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
                new_text += "<xhtml:li>" + lines.strip() + "</xhtml:li>"
            replace_exp = new_text.rstrip()
        elif search_exp == "{solution_text}":
            new_text = "_" + '_'.join(
                module_path_from_root_dir(self.module_dir,
                                          self.module_set_dir))\
                       + "_SOLUTION_MSG"
            replace_exp = new_text
        if replace_exp == '' and search_exp in forbidden_empty:
            raise EmptyTagGroupXMLError(search_exp)

        for cnt, line in enumerate(section):
            if search_exp in line:
                section[cnt] = line.replace(search_exp, replace_exp)

    def add_value_tag(self):
        """The function adds VALUE tag in group.xml file"""
        value_tag = []
        check_export_tag = []

        check_export_tag.append(xml_tags.RULE_SECTION_VALUE_IMPORT)
        for key, val in xml_tags.DIC_VALUES.items():
            value_tag.append(xml_tags.VALUE)
            if key == 'current_directory':
                val = '/'.join(module_path_from_root_dir(self.module_dir,
                                                         self.module_set_dir))
                val = 'SCENARIO/' + val
            if key == 'module_path':
                val = '_'.join(module_path_from_root_dir(self.module_dir,
                                                         self.module_set_dir))
            self.update_values_list(value_tag, "{value_name}", val)
            self.update_values_list(value_tag, "{val}", key.lower())
            check_export_tag.append(xml_tags.RULE_SECTION_VALUE)
            self.update_values_list(check_export_tag, "{value_name_upper}",
                                    key.upper())
            self.update_values_list(check_export_tag, "{val}", key.lower())
        for key, val in xml_tags.GLOBAL_DIC_VALUES.items():
            check_export_tag.append(xml_tags.RULE_SECTION_VALUE_GLOBAL)
            self.update_values_list(check_export_tag, "{value_name_upper}",
                                    key.upper())
            self.update_values_list(check_export_tag, "{value_name}", key)

        return value_tag, check_export_tag

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
            self.mh.check_inplace_risk(prefix=check,
                                       check_func=check_func[check])
        self.update_values_list(self.rule, "{scap_name}",
                                settings.check_script)
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
        self.update_values_list(self.rule, "{" + k + "}",
                                settings.check_script)

    def prepare_sections(self):
        """
        The function prepares all tags needed for generation group.xml file.
        """
        for ini_filepath, ini_file_content in iter(self.ini_files.items()):
            if ini_filepath.endswith("group.ini"):
                self.rule.append(xml_tags.GROUP_INI)
                self.update_values_list(self.rule, '{group_title}',
                                        ini_file_content['group_title'])
                self.update_values_list(self.rule, '{group_value}', "")
            else:
                self.rule.append(xml_tags.CONTENT_INI)
                self.create_xml_from_ini(ini_filepath, ini_file_content)
                self.update_values_list(self.rule, "{select_rules}",
                                        ' '.join(self.select_rules))
            self.update_values_list(self.rule, "{main_dir}",
                                    '_'.join(module_path_from_root_dir(
                                        self.module_dir,
                                        self.module_set_dir)))
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
        """
        Function updates a check_script

        @param {dict} key - options and values from ini file:
            {option1: value, option2: value, ...}
        @param {str} name - 'check_script'
        """
        self.check_script_modification(key, name)
        self.update_values_list(self.select_rules, "{scap_name}",
                                settings.check_script)

    def fnc_check_description(self, key, name):
        """ Function updates a check_description """
        if name in key and key[name] is not None:
            escaped_text = self._update_check_description(key[name])
            self.update_values_list(self.rule, "{check_description}",
                                    escaped_text)
        else:
            self.update_values_list(self.rule, "{check_description}", "")

    def fnc_solution_text(self, *_):
        """
        Function updates a solution text.

        @param {dict} key - options and values from ini file:
            {option1: value, option2: value, ...}
        @param {str} name - 'solution'
        """
        self.mh.check_scripts('solution')
        self.update_values_list(self.rule, "{solution_text}", "")

    def fnc_update_mode(self, name):
        """
        Function update <upgrade_path>/<migrate.conf|update.conf> files
        migrate_xccdf_path
        :param key:
        :param name:
        :return:
        """

        content = "{rule}{main_dir}_{name}".format(
            rule=xml_tags.TAG_RULE,
            main_dir='_'.join(module_path_from_root_dir(self.module_dir,
                                                        self.module_set_dir)),
            name=settings.check_script)
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
            escaped_text = html_escape(key[name])
            self.update_values_list(self.rule, "{" + name + "}", escaped_text)

    def create_xml_from_ini(self, ini_filepath, ini_content):
        """
        Creates group.xml file from INI file. All tags are replaced by function
        update_value_list. Function also checks whether check script fulfills
        all criteria

        @param {str} ini_filepath - real path of ini file
        @param {dict} ini_content - options and values from ini file:
            {option1: value, option2: value, ...}
        @throws {IOError}
        """
        self.select_rules.append(xml_tags.SELECT_TAG)
        update_fnc = {
            'config_file': self.fnc_config_file,
            'check_script': self.fnc_check_script,
            'check_description': self.fnc_check_description,
            'solution': self.fnc_solution_text,
            'content_title': self.update_text,
            'content_description': self.update_text,
        }
        ModuleHelper.check_required_fields(ini_filepath, ini_content)
        self.mh = ModuleHelper(os.path.dirname(ini_filepath))

        self.update_values_list(self.rule, "{rule_tag}",
                                ''.join(xml_tags.RULE_SECTION))
        value_tag, check_export_tag = self.add_value_tag()
        self.update_values_list(self.rule, "{check_export}",
                                ''.join(check_export_tag))
        self.update_values_list(self.rule, "{group_value}",
                                ''.join(value_tag))

        for k, function in iter(update_fnc.items()):
            try:
                function(ini_content, k)
            except IOError as e:
                err_msg = "Invalid value of the field '%s' in INI file" \
                          " '%s'\n'%s': %s\n" % (k, ini_filepath,
                                                 ini_content[k], e.strerror)
                raise IOError(err_msg)

        self.update_values_list(
            self.rule, '{group_title}',
            html_escape(ini_content['content_title'])
        )
        if 'mode' not in ini_content:
            self.fnc_update_mode('migrate, upgrade')
        else:
            self.fnc_update_mode(ini_content['mode'])
