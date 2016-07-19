
from __future__ import unicode_literals, print_function
import logging
import os
import sys
from preup import settings


class LoggerHelper(object):
    """
    Helper class for setting up a logger
    """

    @staticmethod
    def get_basic_logger(logger_name, level=logging.DEBUG):
        """
        Sets-up a basic logger without any handler
        :param logger_name: Logger name
        :param level: severity level
        :return: created logger
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        return logger

    @staticmethod
    def add_stream_handler(logger, level=None):
        """
        Adds console handler with given severity.
        :param logger: logger object to add the handler to
        :param level: severity level
        :return: None
        """
        console_handler = logging.StreamHandler(sys.stdout)
        if level:
            console_handler.setLevel(level)
        logger.addHandler(console_handler)

    @staticmethod
    def add_file_handler(logger, path, formatter=None, level=None):
        """
        Adds FileHandler to a given logger
        :param logger: Logger object to which the file handler will be added
        :param path: Path to file where the debug log will be written
        :return: None
        """
        file_handler = logging.FileHandler(path, 'w')
        if level:
            file_handler.setLevel(level)
        if formatter:
            file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

logger = LoggerHelper.get_basic_logger('preupgrade-assistant')
logger_debug = LoggerHelper.get_basic_logger('preupgrade-assistant-debug')
logger_report = LoggerHelper.get_basic_logger('preupgrade-assistant-report', logging.DEBUG)


def log_message(message, new_line=True, level=logging.INFO):
    """ if verbose, log `msg % args` to stdout """
    if int(sys.version_info[0]) == 2:
        sys.stdout.write(message.encode(settings.defenc))
        sys.stdout.flush()
        # This is used in case that we do not want to print the new line
        if new_line:
            sys.stdout.write("\n")
            sys.stdout.flush()
    else:
        endline = "\n" if new_line else ""
        print(message, end=endline, file=sys.stdout, flush=True)

    logger_debug.log(level, message)


def log_report_message(message, new_line=True, level=logging.INFO):
    """ if verbose, log `msg % args` to stdout """
    if int(sys.version_info[0]) == 2:
        sys.stdout.write(message.encode(settings.defenc))
        sys.stdout.flush()
        # This is used in case that we do not want to print the new line
        if new_line:
            sys.stdout.write("\n")
            sys.stdout.flush()
    else:
        endline = "\n" if new_line else ""
        print(message, end=endline, file=sys.stdout, flush=True)

    logger_report.log(level, message)

