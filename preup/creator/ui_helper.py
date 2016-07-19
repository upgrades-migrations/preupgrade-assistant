# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

import os
import ConfigParser
import shutil
import sys
import six

from distutils.util import strtobool
from preup.utils import FileHelper, SystemIdentification
from preup.creator import settings

from preup.settings import content_file as ALL_XCCDF_XML
section = 'preupgrade'


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
                print ('You have to type [y]es or [n]o.')
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

    def _init_dict(self):
        self.content_dict['content_description'] = ''

    @staticmethod
    def check_path(path, msg):
        if os.path.exists(path):
            choice = get_user_input(msg)
            if not choice:
                return None
        return True

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
        return os.path.join(self.get_upgrade_path(), self.content_path)

    def get_upgrade_path(self):
        if self.upgrade_path.startswith("/"):
            return self.upgrade_path
        return os.path.join(os.getcwd(), self.upgrade_path)

    def specify_upgrade_path(self):
        if self.upgrade_path is None:
            self.upgrade_path = get_user_input(settings.upgrade_path, any_input=True)

        if self.upgrade_path is True or self.upgrade_path == "":
            print ("Scenario is mandatory. You have to specify it.")
            return None

        if not SystemIdentification.get_valid_scenario(self.upgrade_path):
            if self.content_path is None:
                self.content_path = self.upgrade_path
            print ("Scenario '%s' is not valid.\nIt has to be like RHEL6_7 or CentOS7_RHEL7." % self.content_path)
            return None

        message = 'Path %s already exists.\nDo you want to create a content there?' % self.upgrade_path
        if UIHelper.check_path(self.get_upgrade_path(), message) is None:
            return None

        return True

    def prepare_content_env(self):
        self.content_path = os.path.join(self.get_group_name(), self.get_content_name())

    def get_content_info(self):
        self._group_name = get_user_input(settings.group_name, any_input=True)
        if self._group_name is True:
            self._group_name = settings.default_group
        self._content_name = get_user_input(settings.content_name, any_input=True)
        if self._content_name is True:
            self._content_name = settings.default_module
        self.prepare_content_env()
        if os.path.exists(self.get_content_path()):
            message = "Content %s already exists.\nDo you want to overwrite them?" % os.path.join(self.upgrade_path,
                                                                                                  self.content_path)
            if UIHelper.check_path(os.path.join(self.upgrade_path, self.content_path), message):
                # User would like to overwrite the content. We will delete them and and make newerone.
                self.refresh_content = True
        else:
            os.makedirs(self.get_content_path())
        checkscript = get_user_input(settings.check_script, any_input=True)
        if checkscript is True:
            checkscript = settings.default_script_name
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
        for key, val in six.iteritems(self.content_dict):
            if val is not None:
                config.set(section, key, val)

        self.content_ini = self.get_content_name() + '.ini'
        ini_path = os.path.join(self.get_content_path(), self.get_content_ini_file())
        try:
            f = open(ini_path, 'wb')
            config.write(f)
            f.close()
        except IOError:
            print ('We have a problem with writing content file %s to disc' % ini_path)
            raise

    def _create_check_script(self):
        if self.check_script:
            FileHelper.write_to_file(os.path.join(self.get_content_path(),
                                                  self.get_check_script()),
                                     'wb',
                                     settings.temp_check_script)
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
        group_ini = os.path.join(self.get_upgrade_path(), self.get_group_name(), file_name)
        if os.path.exists(group_ini):
            return
        try:
            f = open(group_ini, 'wb')
            config.write(f)
            f.close()
        except IOError:
            print ('We have a problem with writing %s file to disc' % group_ini)
            raise

    def create_final_content(self):
        try:
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
        print (settings.summary_title)
        print (settings.summary_directory % self.get_content_path())
        print (settings.summary_ini % os.path.join(content_path, self.get_content_ini_file()))
        print (settings.summary_check % os.path.join(content_path, self.get_check_script()))
        print (settings.summary_solution % os.path.join(content_path, self.get_solution_file()))
        print (settings.text_for_testing % (content_path, os.path.join(result_content_path, ALL_XCCDF_XML)))

    def take_manadatory_info(self):
        try:
            if self.specify_upgrade_path() is None:
                return 1
            self.get_content_info()
            if self.refresh_content:
                shutil.rmtree(self.get_content_path())
                os.makedirs(self.get_content_path())

            if self.create_final_content() is None:
                return 1
            self._brief_summary()
        except KeyboardInterrupt:
            print ('\n Content creation was interrupted by user.\n')
            shutil.rmtree(self.get_content_path())
