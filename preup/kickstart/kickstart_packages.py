# -*- coding: utf-8 -*-

"""
Class creates a set of packages for migration scenario
"""

import os
from preup.utils import get_file_content


class YumGroupManager(object):
    """more intelligent dict; enables searching in yum groups"""
    def __init__(self):
        self.groups = {}

    def add(self, group):
        self.groups[group.name] = group

    def find_match(self, packages):
        """is there a group whose packages are subset of argument 'packages'?"""
        groups = []
        for group in self.groups.itervalues():
            if len(group.required) != 0:
                if group.match(packages):
                    groups.append(group)
        return groups

    def __str__(self):
        return "%s: %d groups" % (self.__class__.__name__, len(self.groups.values()))


class YumGroup(object):
    def __init__(self, name, mandatory, default, optional):
        self.name = name
        self.mandatory = mandatory
        self.mandatory_set = set(mandatory)
        self.default = default
        self.optional = optional
        self.required = set(mandatory + default)
        self.missing_installed = []

    def __str__(self):
        return "%s (%d required packages)" % (self.name, len(self.required))

    def __repr__(self):
        return "<%s: M:%s D:%s O:%s>" % (self.name, self.mandatory, self.default, self.optional)

    def match(self, packages):
        found = self.required.issubset(packages)
        if self.name == 'core':
            return True
        if not found:
            if len(self.required) == 1:
                return False
            cnt_pkgs = 0
            for pkg in self.required:
                if pkg not in packages:
                    cnt_pkgs += 1
                self.missing_installed.append(pkg)
            if len(self.required) == int(cnt_pkgs):
                return False
            found = True
        return found

    def exclude_mandatory(self, packages):
        # New set with elements in packages but not in self.required
        return packages.difference(self.required)

    def exclude_optional(self, packages):
        # New set with elements in packages but not in self.optional
        return packages.difference(self.optional)


class YumGroupGenerator(object):
    """class for aggregating packages into yum groups"""

    def __init__(self, package_list, removed_packages, *args, **kwargs):
        """
        we dont take info about groups from yum, but from dark matrix, format is:

        group_name | mandatory packages | default packages | optional

        package_list is a list of packages which should aggregated into groups
        args is a list of filepaths to files where group definitions are stored
        """
        self.packages = set(package_list)
        self.removed_packages = set(removed_packages)
        self.gm = YumGroupManager()
        self.group_def_fp = []
        for p in args:
            if os.path.exists(p):
                self.group_def_fp.append(p)
                self._read_group_info()

    def _read_group_info(self):
        def get_packages(s):
            # get rid of empty strings
            return [x for x in s.strip().split(',') if x]

        for fp in self.group_def_fp:
            lines = get_file_content(fp, 'r', True)
            for line in lines:
                stuff = line.split('|')
                name = stuff[0].strip()
                mandatory = get_packages(stuff[1])
                default = get_packages(stuff[2])
                optional = get_packages(stuff[3])
                # why would we want empty groups?
                if mandatory or default or optional:
                    yg = YumGroup(name, mandatory, default, optional)
                    self.gm.add(yg)

    def remove_packages(self):
        for pkg in self.removed_packages:
            if pkg in self.packages:
                self.packages.remove(pkg)

    def get_list(self):
        groups = self.gm.find_match(self.packages)
        output_groups = []
        output_packages = self.packages
        missing_installed = []
        for group in groups:
            if len(group.required) != 0:
                output_groups.append('@'+group.name)
                missing_installed.extend([x + ' # group ' + group.name for x in group.missing_installed])
                output_packages = group.exclude_mandatory(output_packages)
                output_packages = group.exclude_optional(output_packages)
        output_groups.sort()
        output_packages = list(output_packages)
        output_packages.sort()
        return output_groups, output_packages, missing_installed


class PackagesHandling(object):
    """class for replacing/updating package names"""

    def __init__(self, package_list, obsoleted, *args, **kwargs):
        """
        we dont take info about groups from yum, but from dark matrix, format is:

        group_name | mandatory packages | default packages | optional

        package_list is a list of packages which should aggregated into groups
        args is a list of filepaths to files where group definitions are stored
        """
        self.packages = package_list
        self.obsoleted = obsoleted

    def replace_obsolete(self):
        # obsolete list has format like
        # old_pkg|required-by-pkg|obsoleted-by-pkgs|repo-id
        for pkg in self.obsoleted:
            fields = pkg.split('|')
            self.packages.append(fields[2])

    def get_packages(self):
        return self.packages
