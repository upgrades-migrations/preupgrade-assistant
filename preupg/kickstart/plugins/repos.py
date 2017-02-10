# -*- coding: utf-8 -*-

"""
Class creates a set of packages for migration scenario
"""

import os

from preupg.utils import FileHelper
from preupg.kickstart.application import BaseKickstart
from preupg import settings


class ReposHandling(BaseKickstart):
    """class for replacing/updating package names"""

    def __init__(self, handler):
        """
        """
        self.handler = handler
        self.repos = ReposHandling.get_kickstart_repo('available-repos')

    @staticmethod
    def get_kickstart_repo(filename):
        """
        returns dictionary with names and URLs
        :param filename: filename with available-repos
        :return: dictionary with enabled repolist
        """
        try:
            lines = FileHelper.get_file_content(
                os.path.join(settings.KS_DIR, filename), 'rb', method=True
            )
        except IOError:
            return None
        lines = [x for x in lines
                 if not x.startswith('#') and not x.startswith(' ')]
        if not lines:
            return None
        repo_dict = {}
        for line in lines:
            fields = line.split('=')
            repo_dict[fields[0]] = fields[2]
        return repo_dict

    def update_repositories(self):
        if self.repos:
            for key, value in iter(self.repos.items()):
                self.handler.repo.dataList().append(
                    self.handler.RepoData(name=key, baseurl=value.strip())
                )

    def run_module(self, *args, **kwargs):
        self.update_repositories()
