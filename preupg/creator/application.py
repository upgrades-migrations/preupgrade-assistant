# -*- coding: utf-8 -*-
"""
The application module serves for creating a content
"""

from preupg.logger import logging, LoggerHelper, logger
from preupg.creator.ui_helper import UIHelper


class Application(object):

    """Class for oscap binary and reporting results to UI"""

    def __init__(self, conf):
        """conf is preupg.conf.Conf object, contains configuration"""
        self.conf = conf
        if self.conf.debug is None:
            LoggerHelper.add_stream_handler(logger, logging.INFO)
        else:
            LoggerHelper.add_stream_handler(logger, logging.DEBUG)
        self.ui_helper = UIHelper(self.conf.maindir)

    def run(self):
        self.ui_helper.take_manadatory_info()
