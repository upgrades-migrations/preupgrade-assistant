# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

import os
import ConfigParser
import shutil
import sys

from distutils.util import strtobool
from preupg.utils import FileHelper, ModuleSetUtils
from preupg.creator import settings

from preupg.settings import content_file as ALL_XCCDF_XML

section = 'preupgrade'
PROPERTIES_FILE_NAME = 'properties.ini'


def get_user_input(message, default_yes=True, any_input=False):
    """
    Function for command line messages

    :param message: prompt string
    :param default_yes: If the default value is YES
    :param any_input: if True, return input without checking it first
    :return: True or False, based on user's input
    """
    choice = '[Y/n]'

    if any_input:
        msg = '{0} '.format(message)
    else:
        msg = '{0} {1}? '.format(message, choice)

    while True:
        if int(sys.version_info[0]) == 2:
            user_input = raw_input(msg)
        else:
            user_input = input(msg)

        if not user_input:
            if default_yes:
                return True
            else:
                return False
        if not any_input:
            try:
                user_input = strtobool(user_input)
            except ValueError:
                print('You have to type [y]es or [n]o.')
                continue

        return user_input


class UIHelper(object):

    def __init__(self, upgrade_path=None):
        self.content_dict = {}
        self.upgrade_path = upgrade_path
        self._group_name = ""
        self._content_name = ""
        self.content_path = None
        self.content_ini = ""
        self.check_script = True
        self.solution_file = True
        self.refresh_content = False
        self.script_type = None
        # properties.ini
        self.properties_ini_path = None
        self.src_version = None
        self.dst_version = None

    def _init_dict(self):
        self.content_dict['content_description'] = ''

    def get_group_name(self):
        return self._group_name

    def get_content_name(self):
        return self._content_name

    def _get_dict_value(self, name):
        try:
            return self.content_dict[name]
        except KeyError:
            return None

    def get_check_script(self):
        return self._get_dict_value('check_script')

    def get_solution_file(self):
        return self._get_dict_value('solution')

    def get_content_ini_file(self):
        return self.content_ini

    def get_content_path(self):
        if self.content_path is None:
            return None
        return os.path.join(self.get_upgrade_path(), self.content_path)

    def get_upgrade_path(self):
        if self.upgrade_path is None:
            return None
        if self.upgrade_path.startswith("/"):
            return self.upgrade_path
        return os.path.join(os.getcwd(), self.upgrade_path)

    def specify_upgrade_path(self):
        if self.upgrade_path is None:
            self.upgrade_path = get_user_input(settings.upgrade_path,
                                               any_input=True)

        if not UIHelper.is_valid_string(self.upgrade_path):
            print("The scenario is mandatory. You have to specify it.")
            return None

        message = 'The path %s already exists.\nDo you want to create a module there?' % self.upgrade_path
        if UIHelper.check_path(self.get_upgrade_path(), message) is None:
            return None

        return True

    def prepare_content_env(self):
        self.content_path = os.path.join(self.get_group_name(),
                                         self.get_content_name())

    def properties_ini(self):
        """ If properties.ini file doesnt exist ask user for OS versions """
        self.properties_ini_path = os.path.join(
            self.get_upgrade_path(),
            PROPERTIES_FILE_NAME)
        if not self.properties_ini_exists():
            self.get_properties_ini_versions()  # ask user for versions

    def properties_ini_exists(self):
        if self.properties_ini_path:
            return os.path.isfile(self.properties_ini_path)
        return False

    def get_properties_ini_versions(self):
        """
        Asks user for src,dst OS versions, while options are mandatory user
        input is required
        """
        while not self.src_version:
            self.src_version = UIHelper.ask_about_version_number(
                settings.prop_src_version,
                "The major source OS version is mandatory.")
        while not self.dst_version:
            self.dst_version = UIHelper.ask_about_version_number(
                settings.prop_dst_version,
                "The major destination OS version is mandatory.")

    def get_script_type(self):
        while True:
            options = ['sh', 'py']
            self.script_type = get_user_input(settings.type_check_script, any_input=True)
            if self.script_type is True:
                self.script_type = "sh"
                break
            if self.script_type not in options:
                print("Select either 'sh or 'py'.")
                continue
            else:
                break
        if self.script_type == "sh":
            message = settings.check_script % settings.default_bash_script_name
        else:
            message = settings.check_script % settings.default_python_script_name
        checkscript = get_user_input(message, any_input=True)
        if checkscript is True:
            if self.script_type == "sh":
                checkscript = settings.default_bash_script_name
            else:
                checkscript = settings.default_python_script_name
        return checkscript

    def get_content_info(self):
        self._group_name = get_user_input(settings.group_name, any_input=True)
        if self._group_name is True:
            self._group_name = settings.default_group
        self._content_name = get_user_input(settings.content_name, any_input=True)
        if self._content_name is True:
            self._content_name = settings.default_module
        self.prepare_content_env()
        if os.path.exists(self.get_content_path()):
            message = "The module %s already exists.\nDo you want to overwrite them?" % os.path.join(self.upgrade_path,
                                                                                                  self.content_path)
            if UIHelper.check_path(os.path.join(self.upgrade_path, self.content_path), message):
                # User would like to overwrite the content. We will delete them and and make newerone.
                self.refresh_content = True
        else:
            os.makedirs(self.get_content_path())
        checkscript = self.get_script_type()
        if UIHelper.check_path(os.path.join(self.get_content_path(), checkscript),
                               settings.check_path % checkscript) is None:
            self.check_script = False
        self.content_dict['check_script'] = checkscript
        solution = get_user_input(settings.solution_text, any_input=True)
        if solution is True:
            solution = settings.default_solution_name
        if UIHelper.check_path(os.path.join(self.get_content_path(), solution),
                               settings.check_path % solution) is None:
            self.solution_file = False
        self.content_dict['solution'] = solution
        self.content_dict['content_title'] = get_user_input(settings.content_title, any_input=True)
        response = get_user_input(settings.content_desc)
        if not response:
            self.content_dict['content_description'] = None
        else:
            desc = get_user_input(settings.content_desc_text, any_input=True)
            self.content_dict['content_description'] = desc

    def _create_ini_file(self):
        """
        INI file should look like
        [preupgrade]
        content_title: Bacula Backup Software
        author: Petr Hracek <phracek@redhat.com>
        content_description: This module verifies the directory permissions for the Bacula service.
        solution: bacula.txt
        check_script: check.sh
        applies_to: bacula-common
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.add_section(section)
        for key, val in iter(self.content_dict.items()):
            if val is not None:
                config.set(section, key, val)

        self.content_ini = self.get_content_name() + '.ini'
        ini_path = os.path.join(self.get_content_path(), self.get_content_ini_file())
        UIHelper.write_config_to_file(ini_path, config)

    def _create_check_script(self):
        if self.check_script:
            if self.script_type == "sh":
                content = settings.temp_bash_script
            else:
                content = settings.temp_python_script
            FileHelper.write_to_file(os.path.join(self.get_content_path(),
                                                  self.get_check_script()),
                                     'wb',
                                     content)
            os.chmod(os.path.join(self.get_content_path(),
                                  self.get_check_script()),
                     0755)

    def _create_solution_file(self):
        if self.solution_file:
            FileHelper.write_to_file(os.path.join(self.get_content_path(), self.get_solution_file()), 'wb', '')

    def _create_group_ini(self):
        """
        INI file should look like
        [preupgrade]
        group_title = <some title>
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.add_section(section)
        config.set(section, 'group_title', 'Title for %s ' % self.get_group_name())

        file_name = 'group.ini'
        group_ini = os.path.join(self.get_upgrade_path(),
                                 self.get_group_name(),
                                 file_name)
        if os.path.exists(group_ini):
            return
        UIHelper.write_config_to_file(group_ini, config)

    def create_properties_ini(self):
        """
        Create properties.ini inside module set directory in format:

        [preupgrade-assistant-modules]
        src_major_version = <user_input>
        dst_major_version = <user_input>
        """
        if not self.properties_ini_exists():
            section = 'preupgrade-assistant-modules'

            config = ConfigParser.RawConfigParser()
            config.add_section(section)
            config.set(section, 'src_major_version', self.src_version)
            config.set(section, 'dst_major_version', self.dst_version)

            UIHelper.write_config_to_file(self.properties_ini_path, config)

    def create_final_content(self):
        try:
            self.create_properties_ini()
            self._create_group_ini()
            self._create_ini_file()
        except IOError:
            return None

        self._create_check_script()
        self._create_solution_file()
        return True

    def _brief_summary(self):
        content_path = os.path.join(self.upgrade_path, self.get_group_name(), self.get_content_name())
        result_content_path = os.path.join(self.upgrade_path + '-results',
                                           self.get_group_name(),
                                           self.get_content_name())
        print(settings.summary_title)
        print(settings.summary_directory % self.get_content_path())
        print(settings.properties_ini % (self.properties_ini_path))
        print(settings.summary_ini % os.path.join(content_path,
                                                  self.get_content_ini_file()))
        print(settings.summary_check % os.path.join(content_path,
                                                    self.get_check_script()))
        print(settings.summary_solution % os.path.join(content_path,
                                                       self.get_solution_file()))
        print(settings.text_for_testing % (content_path,
                                           os.path.join(result_content_path,
                                                        ALL_XCCDF_XML)))

    def take_manadatory_info(self):
        try:
            if self.specify_upgrade_path() is None:
                return 1

            self.properties_ini()

            self.get_content_info()
            if self.refresh_content:
                shutil.rmtree(self.get_content_path())
                os.makedirs(self.get_content_path())
            if self.create_final_content() is None:
                return 1
            self._brief_summary()
        except KeyboardInterrupt:
            if self.get_content_path() is not None:
                shutil.rmtree(self.get_content_path())
            print('\n Content creation was interrupted by user.\n')

    @staticmethod
    def check_path(path, msg):
        if os.path.exists(path):
            choice = get_user_input(msg)
            if not choice:
                return None
        return True

    @staticmethod
    def is_valid_string(string):
        if isinstance(string, basestring) and bool(string.strip()):
            return True
        return False

    @staticmethod
    def ask_about_version_number(msg, err_msg):
        version = get_user_input(msg, any_input=True)
        if not UIHelper.is_valid_string(version):
            print(err_msg)
            return False
        return version

    @staticmethod
    def write_config_to_file(file_path, config):
        """
        Create config file

        @param {str} file_path - path of new config file
        @param {RawConfigParser} config - configuration object with config data
        @throws {IOError}
        """
        try:
            with open(file_path, 'wb') as f:
                config.write(f)
        except IOError:
            print('An error occured while writing to the {0} file!'.format(
                file_path))
            raise
