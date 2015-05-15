# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

from __future__ import print_function, unicode_literals
import base64
import shutil
import os
import six

from pykickstart.parser import KickstartError, KickstartParser, Script
from pykickstart.version import makeVersion
from pykickstart.constants import KS_SCRIPT_POST
from preup.logger import log_message
from preup import settings
from preup.utils import write_to_file, get_file_content


class YumGroupManager(object):
    """more intelligent dict; enables searching in yum groups"""
    def __init__(self):
        self.groups = {}

    def add(self, group):
        self.groups[group.name] = group

    def find_match(self, packages):
        """is there a group whose packages are subset of argument 'packages'?"""
        groups = []
        for group in six.itervalues(self.groups):
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

    def __str__(self):
        return "%s (%d required packages)" % (self.name, len(self.required))

    def __repr__(self):
        return "<%s: M:%s D:%s O:%s>" % (self.name, self.mandatory, self.default, self.optional)

    def match(self, packages):
        return self.required.issubset(packages)

    def exclude_mandatory(self, packages):
        return packages.difference(self.required)


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

    def remove_packages(self, package_list):
        for pkg in self.removed_packages:
            if pkg in package_list:
                package_list.remove(pkg)
        return package_list

    def get_list(self):
        groups = self.gm.find_match(self.packages)
        output = []
        output_packages = self.packages
        for group in groups:
            if len(group.required) != 0:
                output.append('@' + group.name)
                output_packages = group.exclude_mandatory(output_packages)
        output.sort()
        output_packages = list(output_packages)
        output_packages.sort()
        return output + output_packages


class KickstartGenerator(object):
    """Generate kickstart using data from provided result"""
    def __init__(self, kick_start_name):
        self.ks = KickstartGenerator.load_or_default(KickstartGenerator.get_kickstart_path())
        self.kick_start_name = kick_start_name
        self.ks_list = []

    @staticmethod
    def get_kickstart_path():
        return os.path.join(settings.KS_DIR, 'anaconda-ks.cfg')

    @staticmethod
    def load_or_default(system_ks_path):
        """load system ks or default ks"""
        ksparser = KickstartParser(makeVersion())
        try:
            ksparser.readKickstart(system_ks_path)
        except (KickstartError, IOError):
            log_message("Can't read system kickstart at {0}".format(system_ks_path))
            try:
                ksparser.readKickstart(settings.KS_TEMPLATE)
            except AttributeError:
                log_message("There is no KS_TEMPLATE_POSTSCRIPT specified in settings.py")
            except IOError:
                log_message("Can't read kickstart template {0}".format(settings.KS_TEMPLATE))
        return ksparser

    @staticmethod
    def get_package_list(filename):
        """
        content packages/ReplacedPackages is taking care of packages, which were
        replaced/obsoleted/removed between releases. It produces a file with a list
        of packages which should be installed.
        """
        lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        # Remove newline character from list
        lines = [line.strip() for line in lines]
        return lines

    @staticmethod
    def get_kickstart_repo(filename):
        """
        returns dictionary with names and URLs
        :param filename: filename with available-repos
        :return: dictionary with enabled repolist
        """
        lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        repo_dict = {}
        for line in lines:
            fields = line.split('=')
            repo_dict[fields[0]] = fields[2]
        return repo_dict

    @staticmethod
    def get_kickstart_users(filename):
        """
        returns dictionary with names and uid, gid, etc.
        :param filename: filename with Users in /root/preupgrade/kickstart directory
        :return: dictionary with users
        """
        lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        user_dict = {}
        for line in lines:
            fields = line.split(':')
            user_dict[fields[0]] = "%s:%s" % (fields[2], fields[3])
        return user_dict

    def output_packages(self):
        """outputs %packages section"""
        installed_packages = KickstartGenerator.get_package_list('RHRHEL7rpmlist')
        removed_packages = KickstartGenerator.get_package_list('RemovedPkg-optional')
        if not installed_packages or not removed_packages:
            return None
        abs_fps = [os.path.join(settings.KS_DIR, fp) for fp in settings.KS_FILES]
        ygg = YumGroupGenerator(installed_packages, removed_packages, *abs_fps)
        display_package_names = ygg.get_list()
        display_package_names = ygg.remove_packages(display_package_names)
        return display_package_names
        # return display_group_names + display_package_names

    def embed_script(self, tarball):
        tarball_content = get_file_content(tarball, 'rb')
        script_str = ''
        try:
            script_path = settings.KS_TEMPLATE_POSTSCRIPT
        except AttributeError:
            log_message('KS_TEMPLATE_POSTSCRIPT is not defined in settings.py')
            return
        script_str = get_file_content(os.path.join(settings.KS_DIR, script_path), 'rb')
        if not script_str:
            log_message("Can't open script template: {0}".format(script_path))
            return

        script_str = script_str.replace('{tar_ball}', base64.b64encode(tarball_content))

        script = Script(script_str, type=KS_SCRIPT_POST, inChroot=True)
        self.ks.handler.scripts.append(script)

    def save_kickstart(self):
        write_to_file(self.kick_start_name, 'wb', self.ks.handler.__str__())

    def update_kickstart(self, text, cnt):
        self.ks_list.insert(cnt, text)
        return cnt + 1

    @staticmethod
    def copy_kickstart_templates():
        # Copy kickstart files (/usr/share/preupgrade/kickstart) for kickstart generation
        for file_name in settings.KS_TEMPLATES:
            target_name = os.path.join(settings.KS_DIR, file_name)
            source_name = os.path.join(settings.source_dir, 'kickstart', file_name)
            if not os.path.exists(target_name) and os.path.exists(source_name):
                shutil.copy(source_name, target_name)

    def update_repositories(self, repositories):
        for key, value in six.iteritems(repositories):
            self.ks.handler.repo.dataList().append(self.ks.handler.RepoData(name=key, baseurl=value.strip()))

    def update_users(self, users):
        for key, value in six.iteritems(users):
            uid, gid = value.strip().split(':')
            self.ks.handler.user.dataList().append(self.ks.handler.UserData(name=key, uid=uid, gid=gid))

    def get_prefix(self):
        return settings.tarball_prefix + settings.tarball_base

    def get_latest_tarball(self):
        tarball = None
        for directories, dummy_subdir, filenames in os.walk(settings.tarball_result_dir):
            preupg_files = [x for x in sorted(filenames) if x.startswith(self.get_prefix())]
            # We need a last file
            tarball = os.path.join(directories, preupg_files[-1])
        return tarball

    def generate(self):
        packages = self.output_packages()
        if packages:
            self.ks.handler.packages.add(packages)
        self.update_repositories(KickstartGenerator.get_kickstart_repo('available-repos'))
        self.update_users(KickstartGenerator.get_kickstart_users('Users'))
        self.embed_script(self.get_latest_tarball())
        self.save_kickstart()


def main():
    kg = KickstartGenerator()
    #print kg.generate()

    # group.packages() -> ['package', ...]
    #import ipdb ; ipdb.set_trace()
    return

if __name__ == '__main__':
    main()
