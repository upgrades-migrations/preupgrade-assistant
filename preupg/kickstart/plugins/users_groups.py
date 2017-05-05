# -*- coding: utf-8 -*-

"""
Class appends users and groups to kickstart
"""

import os

from preupg import settings
from preupg.utils import FileHelper
from preupg.kickstart.application import BaseKickstart


class UsersGroupsGenerator(BaseKickstart):

    """Generate users"""
    def __init__(self, handler):
        self.handler = handler
        self.user_perm = None
        self.group_perm = None
        self.groups = None

    @staticmethod
    def get_kickstart_users(filename, groups=None, splitter=":"):
        """
        returns dictionary with names and uid, gid, etc.
        :param filename: filename with Users in /root/preupgrade/kickstart directory
        :param groups: dictionary with groups
        :param splitter: delimiter for parsing files
        :return: dictionary with users
        """
        try:
            lines = FileHelper.get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        except IOError:
            return None
        lines = [x for x in lines if not x.startswith('#') and not x.startswith(' ')]
        user_dict = {}
        for line in lines:
            fields = line.strip().split(splitter)
            try:
                user_group = []
                if groups:
                    for key, value in iter(groups.items()):
                        found = [x for x in iter(value.values()) if fields[0] in x]
                        if found:
                            user_group.append(key)
                user_dict[fields[0]] = {}
                user_dict[fields[0]] = {'homedir': fields[5],
                                        'shell': fields[6],
                                        'uid': int(fields[2]),
                                        'gid': int(fields[3]),
                                        'groups': user_group}
            except IndexError:
                pass
        return user_dict

    @staticmethod
    def get_kickstart_groups(filename, splitter=":"):
        """
        returns dictionary with names and uid, gid, etc.
        :param filename: filename with Users in /root/preupgrade/kickstart directory
        :param splitter: delimiter for parsing files
        :return: dictionary with users
        """
        try:
            lines = FileHelper.get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        except IOError:
            return None
        lines = [x for x in lines if not x.startswith('#') and not x.startswith(' ')]
        group_dict = {}
        for line in lines:
            fields = line.split(splitter)
            try:
                group_dict[fields[0]] = {}
                group_dict[fields[0]] = {fields[2]: fields[3].strip().split(',')}
            except IndexError:
                pass
        return group_dict

    def collect_data(self):
        self.group_perm = UsersGroupsGenerator.get_kickstart_groups('Groups')
        self.user_perm = UsersGroupsGenerator.get_kickstart_users('Users', groups=self.group_perm)

    def update_users(self, users):
        if not users:
            return None
        for key, value in iter(users.items()):
            self.handler.user.dataList().append(self.handler.UserData(name=key,
                                                                      uid=int(value['uid']),
                                                                      gid=int(value['gid']),
                                                                      shell=value['shell'],
                                                                      homedir=value['homedir'],
                                                                      groups=value['groups']))

    def update_groups(self, groups):
        if not groups:
            return None
        for key, value in iter(groups.items()):
            for gid in iter(value.keys()):
                self.handler.group.dataList().append(self.handler.GroupData(name=key, gid=gid))

    def filter_kickstart_users(self):
        kickstart_users = {}
        if not self.user_perm:
            return None
        setup_passwd = UsersGroupsGenerator.get_kickstart_users('setup_passwd')
        uidgid = UsersGroupsGenerator.get_kickstart_users('uidgid', splitter='|')
        for user, ids in iter(self.user_perm.items()):
            if setup_passwd:
                if [x for x in iter(setup_passwd.keys()) if user in x]:
                    continue
            if uidgid:
                if [x for x in iter(uidgid.keys()) if user in x]:
                    continue
            kickstart_users[user] = ids
        if not kickstart_users:
            return None
        return kickstart_users

    def filter_kickstart_groups(self):
        kickstart_groups = {}
        if not self.group_perm:
            return None
        uidgid = UsersGroupsGenerator.get_kickstart_users('uidgid', splitter='|')
        for group, ids in iter(self.group_perm.items()):
            if uidgid:
                if [x for x in iter(uidgid.keys()) if group in x]:
                    continue
            kickstart_groups[group] = ids
        if not kickstart_groups:
            return None
        return kickstart_groups

    def run_module(self):
        self.collect_data()
        self.update_users(self.filter_kickstart_users())
        self.update_groups(self.filter_kickstart_groups())
