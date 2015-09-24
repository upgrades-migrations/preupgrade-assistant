# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

from __future__ import print_function
import os
import ConfigParser
import shutil

from preup import utils
from preup.utils import get_valid_scenario
from preup_creator import settings

section = 'preupgrade'


def get_user_value(message, prompt=None):
    return utils.get_message(message=message, prompt=prompt)


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
            accept = ['y', 'yes', 'Y']
            choice = utils.get_message(message=msg, prompt='y/n')
            if choice not in accept:
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
        return os.path.join(os.getcwd(), self.upgrade_path)

    def specify_upgrade_path(self):
        if self.upgrade_path is None:
            self.upgrade_path = get_user_value(settings.upgrade_path)

        if not get_valid_scenario(self.upgrade_path):
            print ("Scenario '%s' is not valid.\nIt has to be like RHEL6_7 or CentOS7_RHEL7." % self.content_path)
            return None

        message = 'Path %s already exists.\nDo you want to create a content there?' % self.upgrade_path
        if UIHelper.check_path(self.get_upgrade_path(), message) is None:
            return None

        return True

    def get_content_info(self):
        self._group_name = get_user_value(settings.group_name)
        self._content_name = get_user_value(settings.content_name)
        self.content_path = os.path.join(self.get_group_name(), self.get_content_name())
        if os.path.exists(self.get_content_path()):
            message = "Content %s already exists.\nDo you want to overwrite them?" % os.path.join(self.upgrade_path,
                                                                                                  self.content_path)
            if UIHelper.check_path(os.path.join(self.upgrade_path, self.content_path), message):
                # User would like to overwrite the content. We will delete them and and make newerone.
                self.refresh_content = True
        else:
            os.makedirs(self.get_content_path())
        checkscript = get_user_value(settings.check_script)
        if UIHelper.check_path(os.path.join(self.get_content_path(), checkscript),
                               settings.check_path % checkscript) is None:
            self.check_script = False
        self.content_dict['check_script'] = checkscript
        solution = get_user_value(settings.solution_text)
        if UIHelper.check_path(os.path.join(self.get_content_path(), solution),
                               settings.check_path % solution) is None:
            self.solution_file = False
        self.content_dict['solution'] = solution
        self.content_dict['content_title'] = get_user_value(settings.content_title)
        response = get_user_value(settings.content_desc, prompt='y/n')
        if response is 'n':
            self.content_dict['content_description'] = None
        else:
            desc = get_user_value(settings.content_desc_text)
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
        for key, val in self.content_dict.iteritems():
            if val is not None:
                config.set(section, key, val)

        self.content_ini = self.get_content_name() + '.ini'
        ini_path = os.path.join(self.get_content_path(), self.content_ini)
        try:
            f = open(ini_path, 'wb')
            config.write(f)
            f.close()
        except IOError:
            print ('We have a problem with writing content file %s to disc' % ini_path)
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
        if self.refresh_content:
            shutil.rmtree(self.get_content_path())
            os.makedirs(self.get_content_path())
        try:
            self._create_group_ini()
            self._create_ini_file()
        except IOError:
            return None
        if self.check_script:
            utils.write_to_file(os.path.join(self.get_content_path(), self.get_check_script()), 'wb', settings.temp_check_script)
            os.chmod(os.path.join(self.get_content_path(), self.get_check_script()), 0755)
        if self.solution_file:
            utils.write_to_file(os.path.join(self.get_content_path(), self.get_solution_file()), 'wb', '')
        return True

    def _brief_summary(self):
        content_path = os.path.join(self.upgrade_path, self.get_group_name(), self.get_content_name())
        print (self.content_ini)
        print (settings.summary_title)
        print (settings.summary_directory % self.get_content_path())
        print (settings.summary_ini % os.path.join(content_path, self.get_content_ini_file()))
        print (settings.summary_check % os.path.join(content_path, self.get_check_script()))
        print (settings.summary_solution % os.path.join(content_path, self.get_solution_file()))

    def take_manadatory_info(self):
        if self.specify_upgrade_path() is None:
            return 1
        self.get_content_info()
        if self.create_final_content() is None:
            return 1
        self._brief_summary()

