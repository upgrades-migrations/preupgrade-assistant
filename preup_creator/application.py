# -*- coding: utf-8 -*-
"""
The application module serves for creating a content
"""

from __future__ import unicode_literals, print_function

from preup.logger import log_message, logging, set_level
from preup_creator.ui_helper import UIHelper


class Application(object):

    """Class for oscap binary and reporting results to UI"""

    def __init__(self, conf):
        """conf is preup.conf.Conf object, contains configuration"""
        self.conf = conf
        if self.conf.debug is None:
            set_level(logging.INFO)
        else:
            set_level(logging.DEBUG)
        self.ui_helper = UIHelper(self.conf.maindir)

    def run(self):
        self.ui_helper.take_manadatory_info()


