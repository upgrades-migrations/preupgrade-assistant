# -*- coding: utf-8 -*-

"""
Class creates a set of packages for migration scenario
"""

import os

from preupg.utils import FileHelper
from preupg.logger import *
from preupg.kickstart.application import BaseKickstart
from preupg import settings


class YumGroupManager(object):
    """more intelligent dict; enables searching in yum groups"""
    def __init__(self):
        self.groups = {}

    def add(self, group):
        self.groups[group.name] = group

    def find_match(self, packages):
        """is there a group whose packages are subset of argument 'packages'?"""
        groups = []
        for group in iter(self.groups.values()):
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
        self.missing = []

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
                self.missing.append(pkg)
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

    def __init__(self, package_list, removed_packages, dependency_list, *args, **kwargs):
        """
        we dont take info about groups from yum, but from dark matrix, format is:

        group_name | mandatory packages | default packages | optional

        package_list is a list of packages which should aggregated into groups
        args is a list of filepaths to files where group definitions are stored
        """
        self.packages = set(package_list)
        self.removed_packages = set(removed_packages)
        self.dependency_list = set(dependency_list)
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
            lines = FileHelper.get_file_content(fp, 'r', True)
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

    def remove_packages(self, packages):
        for pkg in self.removed_packages:
            if pkg in packages:
                packages.remove(pkg)
        return packages

    def remove_dependencies(self, output_packages):
        # Remove dependencies from kickstart
        # New set with elements in output_packages but not in self.dependency_list
        return output_packages.difference(self.dependency_list)

    def get_list(self):
        groups = self.gm.find_match(self.packages)
        output_groups = []
        output_packages = self.packages
        missing_installed = []
        for group in groups:
            if len(group.required) != 0:
                output_groups.append('@'+group.name)
                if self.dependency_list:
                    missing = [x for x in group.missing_installed if x not in self.dependency_list]
                    missing_installed.extend([x + ' # group ' + group.name for x in missing])
                output_packages = group.exclude_mandatory(output_packages)
                output_packages = group.exclude_optional(output_packages)
        output_groups.sort()
        output_packages = list(self.remove_dependencies(output_packages))
        output_packages.sort()
        return output_groups, output_packages, missing_installed


class PackagesHandling(BaseKickstart):
    """class for replacing/updating package names"""

    def __init__(self, handler):
        """
        we dont take info about groups from yum, but from dark matrix, format is:

        group_name | mandatory packages | default packages | optional

        package_list is a list of packages which should aggregated into groups
        args is a list of filepaths to files where group definitions are stored
        """
        self.packages = None
        self.obsoleted = None
        self.handler = handler
        self.installed_dependencies = None
        self.special_pkg_list = None

    def replace_obsolete(self):
        # obsolete list has format like
        # old_pkg|required-by-pkg|obsoleted-by-pkgs|repo-id
        if self.packages:
            for cnt, pkgs in enumerate(self.packages):
                found = [x for x in self.obsoleted if pkgs in x]
                if found:
                    fields = found[0].split('|')
                    self.packages[cnt] = fields[2]

    @staticmethod
    def get_package_list(filename, field=None):
        """
        content packages/ReplacedPackages is taking care of packages, which were
        replaced/obsoleted/removed between releases. It produces a file with a list
        of packages which should be installed.
        """
        full_path_name = os.path.join(settings.KS_DIR, filename)
        if not os.path.exists(full_path_name):
            return []
        lines = FileHelper.get_file_content(full_path_name, 'rb', method=True, decode_flag=True)
        # Remove newline character from list
        package_list = []
        for line in lines:
            # We have to go over all lines and remove all commented.
            if line.startswith('#'):
                continue
            if field is None:
                package_list.append(line.strip())
            else:
                try:
                    # Format of file is like
                    # old-package|required-by-pkgs|replaced-by-pkgs|repoid
                    pkg_field = line.split('|')
                    if pkg_field[field] is not None:
                        package_list.append(pkg_field[field])
                except ValueError:
                    # Line seems to be wrong, go to the next one
                    pass
        return package_list

    @staticmethod
    def get_installed_packages():
        prefix = 'RHRHEL7rpmlist_'
        result_list = []
        list_files = ['kept', 'kept-notbase',
                      'replaced', 'replaced-notbase']
        for l in list_files:
            try:
                result_list.extend(PackagesHandling.get_package_list(prefix + l, 2))
            except IOError:
                log_message("The '%s' file was not found. Skipping the package generation.", (prefix + l))
                return None
        return result_list

    @staticmethod
    def get_installed_dependencies(obsoleted):
        dep_list = []
        deps = PackagesHandling.get_package_list('first_dependencies', field=None)
        for pkg in deps:
            pkg = pkg.strip()
            if pkg.startswith('/'):
                continue
            if '.so' in pkg:
                continue
            if '(' in pkg:
                dep_list.append(pkg.split('(')[0])
                continue
            found = [x for x in obsoleted if pkg in x]
            if found:
                fields = found[0].split('|')
                dep_list.append(fields[2])
            else:
                dep_list.append(pkg.split()[0])

        return dep_list

    def output_packages(self):
        """ outputs %packages section """
        self.packages = PackagesHandling.get_installed_packages()
        if self.packages is None:
            return None, None
        try:
            self.obsoleted = PackagesHandling.get_package_list('RHRHEL7rpmlist_obsoleted')
        except IOError:
            self.obsoleted = []
        try:
            self.special_pkg_list = PackagesHandling.get_package_list('special_pkg_list')
        except IOError:
            self.special_pkg_list = []

        self.installed_dependencies = PackagesHandling.get_installed_dependencies(self.obsoleted)
        self.installed_dependencies = list(set(self.installed_dependencies))
        self.installed_dependencies.sort()
        # remove files which are replaced by another package
        self.replace_obsolete()

        removed_packages = []
        remove_pkg_optional = os.path.join(settings.KS_DIR, 'RemovedPkg-optional')
        if os.path.exists(remove_pkg_optional):
            try:
                removed_packages = FileHelper.get_file_content(remove_pkg_optional, 'r', method=True)
            except IOError:
                return None, None
        # TODO We should think about if ObsoletedPkg-{required,optional} should be used
        if not removed_packages:
            return None, None
        abs_fps = [os.path.join(settings.KS_DIR, fp) for fp in settings.KS_FILES]
        ygg = YumGroupGenerator(self.packages, removed_packages, self.installed_dependencies, *abs_fps)
        groups, self.packages, missing_installed = ygg.get_list()
        self.packages = ygg.remove_packages(self.packages)
        return groups, missing_installed

    def run_module(self, *args, **kwargs):
        (groups, missing_installed) = self.output_packages()
        if self.packages or groups:
            if self.special_pkg_list:
                self.packages.extend(self.special_pkg_list)
            self.handler.packages.packageList = self.packages
            self.handler.packages.groupList = groups
            if missing_installed:
                self.handler.packages.excludedList = missing_installed

