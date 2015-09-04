# -*- coding: utf-8 -*-

"""
This module serves for handling user interactions
"""

from preup import utils


class UIHelper(object):

    def __init__(self):
        self.group_name = ""
        self.content_name = ""

    def specify_group_name(self):
        self.group_name = utils.get_message('Specify a group name which content belongs to (like database):')

    def specify_module_name(self):
        self.content_name = utils.get_message("Specify a module name which will be created (like mysql):")

    def take_manadatory_info(self):
        self.specify_group_name()
        self.specify_module_name()