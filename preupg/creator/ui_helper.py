# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

import os
import ConfigParser
import shutil
import sys

from distutils.util import strtobool
from preupg.utils import FileHelper
from preupg.creator import settings
from preupg import settings as preupgSettings

from preupg.settings import all_xccdf_xml_filename as ALL_XCCDF_XML


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
        return preupgSettings.check_script

    def get_solution_file(self):
        return preupgSettings.solution_txt

    def get_content_ini_file(self):
        return preupgSettings.module_ini

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
            self.upgrade_path = UIHelper\
                .ask_mandatory_string(settings.upgrade_path,
                                      'The scenario is mandatory. '
                                      'You have to specify it.')

        message = 'The path %s already exists.\n'\
            'Do you want to create a module there?' % self.upgrade_path
        if UIHelper.check_path(self.get_upgrade_path(), message) is None:
            return None

        return True

    def prepare_content_env(self):
        self.content_path = os.path.join(self.get_group_name(),
                                         self.get_content_name())

    def get_properties_ini_info(self):
        """ If properties.ini file doesnt exist ask user for OS versions,
        otherwise don't ask anything
        """
        self.properties_ini_path = os.path.join(
            self.get_upgrade_path(),
            preupgSettings.properties_ini)
        if not self.properties_ini_exists():
            self.ask_for_properties_ini_versions()

    def properties_ini_exists(self):
        if self.properties_ini_path:
            return os.path.isfile(self.properties_ini_path)
        return False

    def ask_for_properties_ini_versions(self):
        """
        Asks user for src,dst OS versions, while options are mandatory user
        input is required
        """
        self.src_version = UIHelper.ask_mandatory_string(
            settings.prop_src_version,
            "The major source OS version is mandatory.")
        self.dst_version = UIHelper.ask_mandatory_string(
            settings.prop_dst_version,
            "The major destination OS version is mandatory.")

    def ask_for_script_type(self):
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

    def get_content_info(self):
        self._group_name = get_user_input(settings.group_name, any_input=True)
        if self._group_name is True:
            self._group_name = settings.default_group
        self._content_name = get_user_input(settings.content_name, any_input=True)
        if self._content_name is True:
            self._content_name = settings.default_module
        self.prepare_content_env()
        if os.path.exists(self.get_content_path()):
            message = "The module %s already exists.\n" \
                      "Do you want to overwrite it?" \
                      % os.path.join(self.upgrade_path,
                                     self.content_path)
            if UIHelper.check_path(os.path.join(self.upgrade_path,
                                                self.content_path),
                                   message):
                # User would like to overwrite the module
                self.refresh_content = True
        else:
            os.makedirs(self.get_content_path())

        self.ask_for_script_type()
        checkscript = self.get_check_script()
        if UIHelper.check_path(
                os.path.join(self.get_content_path(), checkscript),
                settings.check_path % checkscript) is None:
            self.check_script = False

        solution = self.get_solution_file()
        if UIHelper.check_path(os.path.join(self.get_content_path(), solution),
                               settings.check_path % solution) is None:
            self.solution_file = False

        self.content_dict['content_title'] = UIHelper\
            .ask_mandatory_string(settings.content_title,
                                  "Module title is mandatory!")

        self.content_dict['content_description'] = UIHelper\
            .ask_mandatory_string(settings.content_desc_text,
                                  "Module description is mandatory!")

    def _create_ini_file(self):
        """
        INI file should look like
        [preupgrade]
        content_title: Bacula Backup Software
        author: Petr Hracek <phracek@redhat.com>
        content_description: This module verifies the directory permissions for the Bacula service.
        applies_to: bacula-common
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.add_section(preupgSettings.prefix)
        for key, val in iter(self.content_dict.items()):
            if val is not None:
                config.set(preupgSettings.prefix, key, val)

        ini_path = os.path.join(self.get_content_path(),
                                self.get_content_ini_file())
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
        config.add_section(preupgSettings.prefix)
        config.set(preupgSettings.prefix, 'group_title', 'Title for %s ' % self.get_group_name())

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
        content_path = os.path.join(self.upgrade_path,
                                    self.get_group_name(),
                                    self.get_content_name())
        generated_all_xccdf_path = os.path.join(self.upgrade_path + '-results',
                                                ALL_XCCDF_XML)
        print(settings.summary_title)
        print(settings.summary_directory % self.get_content_path())
        print(settings.summary_ini
              % os.path.join(content_path, self.get_content_ini_file()))
        print(settings.summary_check
              % os.path.join(content_path, self.get_check_script()))
        print(settings.summary_solution
              % os.path.join(content_path, self.get_solution_file()))
        print(settings.commands_to_use_new_module
              % (self.upgrade_path, generated_all_xccdf_path))

    def take_manadatory_info(self):
        try:
            if self.specify_upgrade_path() is None:
                return 1

            self.get_properties_ini_info()

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
        """Return None when the path exists and user answers No to the
        msg question.
        """
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
    def ask_for_string(msg, err_msg):
        string = get_user_input(msg, any_input=True)
        if not UIHelper.is_valid_string(string):
            print(err_msg)
            return False
        return string

    @staticmethod
    def ask_mandatory_string(msg, err_msg):
        string = False
        while not string:
            string = UIHelper.ask_for_string(msg, err_msg)
        return string

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
