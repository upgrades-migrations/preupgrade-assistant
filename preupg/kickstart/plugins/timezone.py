# -*- coding: utf-8 -*-

"""
Class creates a set of packages for migration scenario
"""

from preupg.utils import FileHelper
from preupg.kickstart.application import BaseKickstart


class TimezoneHandling(BaseKickstart):
    """class for replacing/updating package names"""

    def __init__(self, handler):
        """
        """
        self.handler = handler
        self.timezone = None

    @staticmethod
    def get_kickstart_timezone():
        """
        Contain of the file /etc/sysconfig/clock is ZONE='TIMEZONE'
        :return: list with timezone
        """
        timezone_file = '/etc/sysconfig/clock'
        try:
            lines = FileHelper.get_file_content(timezone_file, 'rb', method=True)
        except IOError:
            return None
        lines = [x for x in lines if x.startswith('ZONE=')]
        if not lines:
            return None
        return lines

    def update_timezone(self):
        if self.timezone:
            for line in self.timezone:
                fields = line.strip().split('=')
                try:
                    self.handler.timezone.timezone = fields[1]
                    self.handler.timezone.isUtc = True
                    break
                except KeyError:
                    pass

    def run_module(self, *args, **kwargs):
        self.timezone = self.get_kickstart_timezone()
        self.update_timezone()
