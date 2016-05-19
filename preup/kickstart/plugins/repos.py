# -*- coding: utf-8 -*-

"""
Class creates a set of packages for migration scenario
"""

import six

from preup.utils import FileHelper
from preup.logger import *
from preup.kickstart.application import BaseKickstart


class ReposHandling(BaseKickstart):
    """class for replacing/updating package names"""

    def __init__(self, handler):
        """
        """
        self.handler = handler
        self.repos = ReposHandling.get_kickstart_repo('available-repos')

    def replace_obsolete(self):
        # obsolete list has format like
        # old_pkg|required-by-pkg|obsoleted-by-pkgs|repo-id
        if self.packages:
            for pkg in self.obsoleted:
                fields = pkg.split('|')
                self.packages.append(fields[2])

    @staticmethod
    def get_kickstart_repo(filename):
        """
        returns dictionary with names and URLs
        :param filename: filename with available-repos
        :return: dictionary with enabled repolist
        """
        try:
            lines = FileHelper.get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        except IOError:
            return None
        lines = [x for x in lines if not x.startswith('#') and not x.startswith(' ')]
        if not lines:
            return None
        repo_dict = {}
        for line in lines:
            fields = line.split('=')
            repo_dict[fields[0]] = fields[2]
        return repo_dict

    def update_repositories(self):
        if self.repos:
            for key, value in six.iteritems(self.repos):
                self.handler.repo.dataList().append(self.handler.RepoData(name=key, baseurl=value.strip()))

    def run_module(self, *args, **kwargs):
        self.update_repositories()
