# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

import os
import ConfigParser

from preup import utils
from preup.utils import get_valid_scenario
from preup_creator import settings

section = 'preupgrade'

class UIHelper(object):

    def __init__(self, upgrade_path):
        self.cwd = os.getcwd()
        self.content_dict = {}
        self.upgrade_path = upgrade_path
        self._group_name = ""
        self._content_name = ""

    def _init_dict(self):
        self.content_dict['content_description'] = ''

    def _check_upgrade_path(self, upgrade_path):
        return get_valid_scenario(upgrade_path)

    def _check_path(self, msg):
        if os.path.exists(self.upgrade_path):
            accept = ['y', 'yes', 'Y']
            choice = utils.get_message(message=msg, prompt='y/n')
            if choice not in accept:
                return None
        return True

    def get_user_value(self, message, prompt=None):
        return utils.get_message(message=message, prompt=prompt)

    def specify_group_name(self):
        self._group_name = self.get_user_value('Specify a group name which content belongs to (like database):')

    def specify_module_name(self):
        self._content_name = self.get_user_value("Specify a module name which will be created (like mysql):")

    def specify_script_name(self):
        self.content_dict['check_script'] = self.get_user_value("Specify a script name which will be used for assessment:")

    def specify_solution_text(self):
        self.content_dict['solution'] = self.get_user_value("Specify a solution name which will be shown for user:")

    def specify_content_title(self):
        self.content_dict['content_title'] = self.get_user_value("Specify a content title:")

    def specify_content_description(self):

        desc = self.get_user_value("Would you like to specify a content description?", prompt='y/n')
        if desc is 'n':
            self.content_dict['content_description'] = None
        else:
            self.content_dict['content_description'] = desc

    def get_group_name(self):
        return self._group_name

    def get_content_name(self):
        return self._content_name

    def get_check_script(self):
        return self.content_dict['check_script']

    def get_solution_file(self):
        return self.content_dict['solution']

    def specify_upgrade_path(self):
        if self.upgrade_path is None:
            self.upgrade_path = self.get_user_value("Specify a upgrade path (like RHEL6_7) where a content will be stored in cwd:")
        self.upgrade_path = os.path.join(self.cwd, self.upgrade_path)
        message = 'Path %s already exists.\nDo you want to create a content there?' % self.upgrade_path
        if self._check_path(message) is None:
            return None

        if not self._check_upgrade_path(self.upgrade_path):
            print ("Scenario '%s' is not valid.\nIt has to be like RHEL6_7 or CentOS7_RHEL7." % self.upgrade_path)
            return None
        return True

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
        for key, val in self.content_dict.iteritems():
            if val is not None:
                config.set(section, key, val)

        file_name = os.path.join(self.get_group_name(), self.get_content_name(), self.get_content_name() + '.ini')
        try:
            f = open(os.path.join(self.upgrade_path, file_name), 'wb')
            config.write(f)
            f.close()
        except IOError:
            print ('We have a problem with writing %s file to disc' % file_name)
            raise

    def _create_group_ini(self):
        """
        INI file should look like
        [preupgrade]
        group_title = <some title>
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.add_section(section)
        config.set(section, 'group_title', 'Title for %s '% self.get_group_name())

        file_name = os.path.join(self.get_group_name(), 'group.ini')
        try:
            f = open(os.path.join(self.upgrade_path, file_name), 'wb')
            config.write(f)
            f.close()
        except IOError:
            print ('We have a problem with writing %s file to disc' % file_name)
            raise

    def create_final_content(self):
        path = os.path.join(self.get_group_name(), self.get_content_name())
        full_path = os.path.join(self.cwd, self.upgrade_path, path)
        if os.path.exists(full_path):
            message = "Content %s already exists.\nDo you want to overwrite them?" % full_path
            if self._check_path(message) is None:
                return None
        else:
            os.makedirs(full_path)
        try:
            self._create_group_ini()
            self._create_ini_file()
        except IOError:
            return None
        utils.write_to_file(os.path.join(full_path, self.get_check_script()), 'wb', settings.temp_check_script)
        os.chmod(os.path.join(full_path, self.get_check_script()), 0755)
        utils.write_to_file(os.path.join(full_path, self.get_solution_file()), 'wb', '')
        return True

    def take_manadatory_info(self):
        if self.specify_upgrade_path() is None:
            return 1
        self.specify_group_name()
        self.specify_module_name()
        self.specify_script_name()
        self.specify_solution_text()
        self.specify_content_title()
        if self.create_final_content() is None:
            return 1

