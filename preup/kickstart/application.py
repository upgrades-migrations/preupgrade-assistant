# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

import base64
import shutil

from pykickstart.constants import *
from pykickstart.parser import *
from pykickstart.version import *

from preup.kickstart.kickstart_packages import YumGroupGenerator, PackagesHandling
from preup.kickstart.kickstart_partitioning import PartitionGenerator
from preup.logger import *
from preup.utils import FileHelper, ProcessHelper


class KickstartGenerator(object):
    """Generate kickstart using data from provided result"""

    def __init__(self, conf, dir_name, kick_start_name):
        self.dir_name = dir_name
        self.ks = None
        self.kick_start_name = kick_start_name
        self.ks_list = []
        self.repos = None
        self.user_perm = None
        self.group_perm = None
        self.latest_tarball = ""
        self.temp_file = '/tmp/part-include'
        self.conf = conf
        self.groups = []
        self.packages = []
        self.part_layout = None
        self.missing_installed = []

    def collect_data(self):
        self._remove_obsolete_data()
        collected_data = True
        self.ks = KickstartGenerator.load_or_default(KickstartGenerator.get_kickstart_path(self.dir_name))
        if self.ks is None:
            collected_data = False
        self.repos = KickstartGenerator.get_kickstart_repo('available-repos')
        self.group_perm = KickstartGenerator.get_kickstart_groups('Groups')
        self.user_perm = KickstartGenerator.get_kickstart_users('Users', groups=self.group_perm)
        self.latest_tarball = self.get_latest_tarball()
        return collected_data

    def _remove_obsolete_data(self):
        if os.path.exists(KickstartGenerator.get_kickstart_path(self.dir_name)):
            lines = FileHelper.get_file_content(KickstartGenerator.get_kickstart_path(self.dir_name), "r", method=True)
            lines = [x for x in lines if not x.startswith('key')]
            FileHelper.write_to_file(KickstartGenerator.get_kickstart_path(self.dir_name), "w", lines)

    @staticmethod
    def get_kickstart_path(dir_name):
        return os.path.join(dir_name, 'anaconda-ks.cfg')

    @staticmethod
    def load_or_default(system_ks_path):
        """ load system ks or default ks """
        ksparser = KickstartParser(makeVersion())
        try:
            ksparser.readKickstart(system_ks_path)
        except (KickstartError, IOError):
            log_message("Can't read system kickstart at %s" % (system_ks_path))
            try:
                ksparser.readKickstart(os.path.join(KickstartGenerator.dir_name, settings.KS_TEMPLATE))
            except AttributeError:
                log_message("There is no KS_TEMPLATE_POSTSCRIPT specified in settings.py")
            except IOError, ioe:
                log_message("Can't read kickstart template %s %s" % (settings.KS_TEMPLATE, ioe))
                return None
        return ksparser

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
            fields = line.split(splitter)
            try:
                user_group = []
                if groups:
                    for key, value in groups.iteritems():
                        found = [x for x in value.itervalues() if fields[0] in x]
                        if found:
                            user_group.append(key)

                user_dict[fields[0]] = {}
                user_dict[fields[0]] = {'homedir': fields[5],
                                        'shell': fields[6],
                                        'uid': fields[2],
                                        'gid': fields[3],
                                        'groups': user_group}
            except IndexError:
                pass
        return user_dict

    @staticmethod
    def get_kickstart_groups(filename, splitter=":"):
        """
        returns dictionary with names and uid, gid, etc.
        :param filename: filename with Users in /root/preupgrade/kickstart directory
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

    @staticmethod
    def _get_sizes(filename):
        part_sizes = {}
        lines = FileHelper.get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True, decode_flag=False)
        lines = [x for x in lines if x.startswith('/')]
        for line in lines:
            fields = line.strip().split(' ')
            part_name = fields[0]
            try:
                size = fields[2]
            except IndexError:
                size = fields[1]
            part_sizes[part_name] = size
        return part_sizes

    @staticmethod
    def get_installed_packages():
        prefix = 'RHRHEL7rpmlist_'
        result_list = []
        list_files = ['kept', 'kept-notbase',
                      'replaced', 'replaced-notbase']
        for l in list_files:
            try:
                result_list.extend(KickstartGenerator.get_package_list(prefix + l, 2))
            except IOError:
                log_message("File '%s' was not found. Skipping package generation.", (prefix + l))
                return None
        return result_list

    @staticmethod
    def get_installed_dependencies():
        dep_list = []
        deps = KickstartGenerator.get_package_list('first_dependencies', field=None)
        for pkg in deps:
            pkg = pkg.strip()
            if pkg.startswith('/'):
                continue
            if '.so' in pkg:
                continue
            if '(' in pkg:
                dep_list.append(pkg.split('(')[0])
                continue
            dep_list.append(pkg.split()[0])

        return dep_list

    def output_packages(self):
        """ outputs %packages section """
        installed_packages = KickstartGenerator.get_installed_packages()
        if installed_packages is None:
            return None
        try:
            obsoleted = KickstartGenerator.get_package_list('RHRHEL7rpmlist_obsoleted')
        except IOError:
            obsoleted = []
        installed_dependencies = KickstartGenerator.get_installed_dependencies()
        ph = PackagesHandling(installed_packages, obsoleted)
        # remove files which are replaced by another package
        ph.replace_obsolete()

        remove_pkg_optional = os.path.join(settings.KS_DIR, 'RemovedPkg-optional')
        if os.path.exists(remove_pkg_optional):
            try:
                removed_packages = FileHelper.get_file_content(remove_pkg_optional, 'r', method=True)
            except IOError:
                return None
        # TODO We should think about if ObsoletedPkg-{required,optional} should be used
        if not installed_packages or not removed_packages:
            return None
        abs_fps = [os.path.join(settings.KS_DIR, fp) for fp in settings.KS_FILES]
        ygg = YumGroupGenerator(ph.get_packages(), removed_packages, installed_dependencies, *abs_fps)
        self.groups, self.packages, self.missing_installed = ygg.get_list()
        self.packages = ygg.remove_packages(self.packages)

    def delete_obsolete_issues(self):
        """ Remove obsolete items which does not exist on RHEL-7 anymore"""
        self.ks.handler.bootloader.location = None

    def embed_script(self, tarball):
        tarball_content = FileHelper.get_file_content(tarball, 'rb', decode_flag=False)
        tarball_name = os.path.splitext(os.path.splitext(os.path.basename(tarball))[0])[0]
        script_str = ''
        try:
            script_path = settings.KS_TEMPLATE_POSTSCRIPT
        except AttributeError:
            log_message('KS_TEMPLATE_POSTSCRIPT is not defined in settings.py')
            return
        script_str = FileHelper.get_file_content(os.path.join(settings.KS_DIR, script_path), 'rb')
        if not script_str:
            log_message("Can't open script template: {0}".format(script_path))
            return

        script_str = script_str.replace('{tar_ball}', base64.b64encode(tarball_content))
        script_str = script_str.replace('{RESULT_NAME}', tarball_name)
        script_str = script_str.replace('{TEMPORARY_PREUPG_DIR}', '/var/tmp/preupgrade')
        script = Script(script_str, type=KS_SCRIPT_POST, inChroot=True)
        self.ks.handler.scripts.append(script)

    def save_kickstart(self):
        kickstart_data = self.ks.handler.__str__()
        FileHelper.write_to_file(self.kick_start_name, 'wb', kickstart_data)

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
                try:
                    shutil.copy(source_name, target_name)
                except IOError:
                    pass

    @staticmethod
    def get_volume_info(filename, first_index, second_index):
        try:
            volume_list = FileHelper.get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True, decode_flag=False)
        except IOError:
            log_message("File %s is missing. Partitioning layout has not to be complete." % filename, level=logging.WARNING)
            return None
        volume_info = {}
        for line in volume_list:
            fields = line.strip().split(':')
            volume_info[fields[first_index]] = fields[second_index]
        return volume_info

    def update_repositories(self, repositories):
        if repositories:
            for key, value in repositories.iteritems():
                self.ks.handler.repo.dataList().append(self.ks.handler.RepoData(name=key, baseurl=value.strip()))

    def update_users(self, users):
        if not users:
            return None
        for key, value in users.iteritems():
            self.ks.handler.user.dataList().append(self.ks.handler.UserData(name=key,
                                                                            uid=value['uid'],
                                                                            gid=value['gid'],
                                                                            shell=value['shell'],
                                                                            homedir=value['homedir'],
                                                                            groups=value['groups']))

    def update_groups(self, groups):
        if not groups:
            return None
        for key, value in groups.iteritems():
            for gid, grouplist in value.iteritems():
                self.ks.handler.group.dataList().append(self.ks.handler.GroupData(name=key, gid=gid))

    def get_partition_layout(self, lsblk, vgs, lvdisplay):
        """
        Returns dictionary with partition and realname and size
        :param filename:  filename with partition_layout in /root/preupgrade/kickstart directory
        :return: dictionary with layout
        """
        lsblk_filename = os.path.join(settings.KS_DIR, lsblk)
        try:
            layout = FileHelper.get_file_content(lsblk_filename, 'rb', method=True, decode_flag=False)
        except IOError:
            log_message("File %s was not generated by a content. Kickstart does not contain partitioning layout" % lsblk_filename)
            self.part_layout = None
            return None
        vg_info = []
        lv_info = []
        if vgs is not None:
            vg_info = KickstartGenerator.get_volume_info(vgs, 0, 5)
        if lvdisplay is not None:
            lv_info = KickstartGenerator.get_volume_info(lvdisplay, 0, 1)
        pg = PartitionGenerator(self.ks.handler, layout, vg_info, lv_info)
        pg.generate_partitioning()
        pg.get_partitioning()

    def get_prefix(self):
        return settings.tarball_prefix + settings.tarball_base

    def get_latest_tarball(self):
        tarball = None
        for directories, dummy_subdir, filenames in os.walk(settings.tarball_result_dir):
            preupg_files = [x for x in sorted(filenames) if x.startswith(self.get_prefix())]
            # We need a last file
            tarball = os.path.join(directories, preupg_files[-1])
        return tarball

    def filter_kickstart_users(self):
        kickstart_users = {}
        if not self.user_perm:
            return None
        setup_passwd = KickstartGenerator.get_kickstart_users('setup_passwd')
        uidgid = KickstartGenerator.get_kickstart_users('uidgid', splitter='|')
        for user, ids in self.user_perm.iteritems():
            if setup_passwd:
                if [x for x in setup_passwd.iterkeys() if user in x]:
                    continue
            if uidgid:
                if [x for x in uidgid.iterkeys() if user in x]:
                    continue
            kickstart_users[user] = ids
        if not kickstart_users:
            return None
        return kickstart_users

    def filter_kickstart_groups(self):
        kickstart_groups = {}
        if not self.groups:
            return None
        uidgid = KickstartGenerator.get_kickstart_users('uidgid', splitter='|')
        for group, ids in self.group_perm.iteritems():
            if uidgid:
                if [x for x in uidgid.iterkeys() if group in x]:
                    continue
            kickstart_groups[group] = ids
        if not kickstart_groups:
            return None
        return kickstart_groups

    def comment_kickstart_issues(self):
        list_issues = [' ', 'group', 'user ', 'repo', 'url', 'rootpw']
        kickstart_data = []
        try:
            kickstart_data = FileHelper.get_file_content(os.path.join(settings.KS_DIR, self.kick_start_name),
                                              'rb',
                                              method=True,
                                              decode_flag=False)
        except IOError:
            log_message("File %s is missing. Partitioning layout has not to be complete." % self.kick_start_name,
                        level=logging.WARNING)
            return None
        for index, row in enumerate(kickstart_data):
            tag = [com for com in list_issues if row.startswith(com)]
            if tag:
                kickstart_data[index] = "#" + row
        FileHelper.write_to_file(self.kick_start_name, 'wb', kickstart_data)

    def generate(self):
        if not self.collect_data():
            log_message("Important data are missing for kickstart generation.", level=logging.ERROR)
            return None
        self.output_packages()
        if self.packages or self.groups:
            self.ks.handler.packages.packageList = self.packages
            self.ks.handler.packages.groupList = self.groups
            if self.missing_installed:
                self.ks.handler.packages.excludedList = self.missing_installed
        self.ks.handler.packages.handleMissing = KS_MISSING_IGNORE
        self.ks.handler.keyboard.keyboard = 'us'
        self.update_repositories(self.repos)
        self.update_users(self.filter_kickstart_users())
        self.update_groups(self.filter_kickstart_groups())
        self.get_partition_layout('lsblk_list', 'vgs_list', 'lvdisplay')
        self.embed_script(self.latest_tarball)
        self.delete_obsolete_issues()
        self.save_kickstart()
        self.comment_kickstart_issues()
        return True

    def main(self):
        if not os.path.exists(os.path.join(settings.result_dir, settings.xml_result_name)):
            log_message("'preupg' command was not run yet. Run them before kickstart generation.")
            return 1

        KickstartGenerator.copy_kickstart_templates()
        dummy_ks = self.generate()
        if dummy_ks:
            log_message(settings.kickstart_text % settings.PREUPGRADE_KS)
        KickstartGenerator.kickstart_scripts()

    @staticmethod
    def kickstart_scripts():
        try:
            lines = FileHelper.get_file_content(os.path.join(settings.common_dir,
                                                        settings.KS_SCRIPTS),
                                           "rb",
                                           method=True)
            for counter, line in enumerate(lines):
                line = line.strip()
                if line.startswith("#"):
                    continue
                if 'is not installed' in line:
                    continue
                cmd, name = line.split("=", 2)
                kickstart_file = os.path.join(settings.KS_DIR, name)
                ProcessHelper.run_subprocess(cmd, output=kickstart_file, shell=True)
        except IOError:
            pass


def run():
    kg = KickstartGenerator()
    #print kg.generate()

    # group.packages() -> ['package', ...]
    #import ipdb ; ipdb.set_trace()
    return
