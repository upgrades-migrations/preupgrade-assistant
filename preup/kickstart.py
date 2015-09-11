# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

from __future__ import print_function, unicode_literals
import base64
import shutil
import os
import six
import re
import random

from pykickstart.parser import KickstartError, KickstartParser, Script
from pykickstart.version import makeVersion
from pykickstart.constants import KS_SCRIPT_POST, KS_SCRIPT_PRE
from preup.logger import log_message, logging
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


class PartitionGenerator(object):
    """Generate partition layout"""
    def __init__(self, layout, vg_info, lvdisplay):
        self.layout = layout
        self.vg_info = vg_info
        self.lvdisplay = lvdisplay
        self.raid_devices = {}
        self.vol_group = {}
        self.logvol = {}
        self.part_dict = {}
        self.parts = {}

    def generate_partitioning(self):
        """
        Returns dictionary with partition and realname and size
        :param filename:  filename with partition_layout in /root/preupgrade/kickstart directory
        :return: dictionary with layout
        """
        pv_name = ""
        index_pv = 1
        crypt = ""
        for index, row in enumerate(self.layout):
            fields = row.strip().split(' ')
            device = fields[0]
            size = fields[3]
            multiple = 1
            if size.endswith('G'):
                multiple = 1000
                # Converting to MB from GB
            size = int(float(size[:-1])) * multiple
            device_type = fields[5]
            try:
                mount = fields[6]
                if mount == '[SWAP]':
                    mount = 'swap'
            except IndexError:
                mount = None
            if device_type == 'disk' or device_type == 'crypt' or device_type == 'rom':
                continue
            if device_type == 'part':
                if not mount:
                    ident = index_pv
                    pv_name = 'pv.%.2d' % int(ident)
                    try:
                        new_row = self.layout[index + 1].strip()
                        if 'raid' in new_row:
                            continue
                        if 'part' in new_row:
                            continue
                        new_row_fields = new_row.split()
                        if 'crypt' in new_row_fields:
                            crypt = ' --encrypted'
                            try:
                                pv_name = new_row_fields[6]
                            except IndexError:
                                pass
                    except IndexError:
                        pass
                    if not self.part_dict.has_key(pv_name):
                        self.part_dict[pv_name] = {}
                    self.part_dict[pv_name]['size'] = size
                    self.part_dict[pv_name]['crypt'] = crypt
                    crypt = ""
                    index_pv += 1
                    continue
                else:
                    device = ''.join([x for x in device if not x.isdigit()])
                    if not self.part_dict.has_key(mount):
                        self.part_dict[mount] = {}
                    self.part_dict[mount]['size'] = size
                    self.part_dict[mount]['device'] = device
                    self.part_dict[mount]['crypt'] = ""
                    continue
            if 'raid' in device_type:
                raid_type = device_type[-1]
                try:
                    new_row_fields = self.layout[index + 1].strip().split()
                    if 'crypt' in new_row_fields:
                        crypt = ' --encrypted --passphrase='
                        fields = self.layout[index + 1].strip().split()
                        mount = fields[6]
                except IndexError:
                    pass
                if not self.raid_devices.has_key(mount):
                    self.raid_devices[mount] = {}
                    self.raid_devices[mount]['raid_devices'] = []
                self.raid_devices[mount]['raid_devices'].append(index_pv)
                self.raid_devices[mount]['level'] = raid_type
                self.raid_devices[mount]['crypt'] = crypt
                crypt = ""
                index_pv += 1
                continue
            if device_type == 'lvm':
                if self.vg_info is None or not self.vg_info:
                    continue
                vg_name = [x for x in six.iterkeys(self.vg_info) if device.startswith(x)][0]
                # Get volume group name
                if not self.vol_group.has_key(vg_name):
                    self.vol_group[vg_name] = {}
                self.vol_group[vg_name]['pesize'] = 4096
                self.vol_group[vg_name]['pv_name'] = pv_name
                if self.lvdisplay is None or not self.lvdisplay:
                    continue
                lv_name = [x for x in six.iterkeys(self.lvdisplay) if x in device][0]
                if not self.logvol.has_key(mount):
                    self.logvol[mount] = {}
                self.logvol[mount]['vgname'] = vg_name
                self.logvol[mount]['size'] = size
                self.logvol[mount]['lv_name'] = lv_name

    def _get_part_devices(self):
        layout = []
        for key, value in sorted(six.iteritems(self.part_dict)):
            crypt = value['crypt']
            try:
                device = " --ondisk=%s" % value['device']
            except KeyError:
                device = ""
            if crypt == "":
                layout.append('part %s --size=%s%s' % (key, value['size'], device))
            else:
                layout.append('part %s --size=%s%s' % (key, value['size'], crypt))
        return layout

    def _get_logvol_device(self):
        layout = []
        for key, value in sorted(six.iteritems(self.logvol)):
            layout.append('logvol %s --vgname=%s --size=%s --name=%s' % (key,
                                                                         value['vgname'],
                                                                         value['size'],
                                                                         value['lv_name']))
        return layout

    def _get_vg_device(self):
        vg_layout = []
        for key, value in six.iteritems(self.vol_group):
            pesize = value['pesize']
            pv_name = value['pv_name']
            vg_layout.append('volgroup %s %s --pesize=%s' % (key, pv_name, pesize))
        return vg_layout

    def _get_raid_devices(self):
        layout = []
        for key, value in six.iteritems(self.raid_devices):
            level = value['level']
            crypt = value['crypt']
            raid_vol = ""
            for index in value['raid_devices']:
                raid = ' raid.%.2d' % int(index)
                layout.append('part%s --grow --size=2048' % raid)
                raid_vol += raid
            layout.append('raid %s --level=%s --device=md%s%s%s' % (key, level, level, raid_vol, crypt))
        return layout

    def get_partitioning(self):
        layout = []
        layout.extend(self._get_part_devices())
        layout.extend(self._get_vg_device())
        layout.extend(self._get_logvol_device())
        layout.extend(self._get_raid_devices())
        return layout


class KickstartGenerator(object):
    """Generate kickstart using data from provided result"""
    def __init__(self, dir_name, kick_start_name):
        self.dir_name = dir_name
        self.ks = None
        self.kick_start_name = kick_start_name
        self.ks_list = []
        self.part_layout = ['clearpart --all']
        self.repos = None
        self.users = None
        self.latest_tarball = ""
        self.temp_file = '/tmp/part-include'

    def collect_data(self):
        collected_data = True
        self.ks = KickstartGenerator.load_or_default(KickstartGenerator.get_kickstart_path(self.dir_name))
        if self.ks is None:
            collected_data = False
        self.repos = KickstartGenerator.get_kickstart_repo('available-repos')
        self.users = KickstartGenerator.get_kickstart_users('Users')
        self.latest_tarball = self.get_latest_tarball()
        return collected_data

    @staticmethod
    def get_kickstart_path(dir_name):
        return os.path.join(dir_name, 'anaconda-ks.cfg')

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
                return None
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
        try:
            lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
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
    def get_kickstart_users(filename, splitter=":"):
        """
        returns dictionary with names and uid, gid, etc.
        :param filename: filename with Users in /root/preupgrade/kickstart directory
        :return: dictionary with users
        """
        try:
            lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True)
        except IOError:
            return None
        lines = [x for x in lines if not x.startswith('#') and not x.startswith(' ')]
        user_dict = {}
        for line in lines:
            fields = line.split(splitter)
            try:
                user_dict[fields[0]] = "%s:%s" % (fields[2], fields[3])
            except IndexError:
                pass
        return user_dict

    @staticmethod
    def _get_sizes(filename):
        part_sizes = {}
        lines = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True, decode_flag=False)
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

    def output_packages(self):
        """outputs %packages section"""
        try:
            installed_packages = KickstartGenerator.get_package_list('RHRHEL7rpmlist')
        except IOError:
            return None
        removed_packages = KickstartGenerator.get_package_list('RemovedPkg-optional')
        # TODO We should think about if ObsoletedPkg-{required,optional} should be used
        if not installed_packages or not removed_packages:
            return None
        abs_fps = [os.path.join(settings.KS_DIR, fp) for fp in settings.KS_FILES]
        ygg = YumGroupGenerator(installed_packages, removed_packages, *abs_fps)
        display_package_names = ygg.get_list()
        display_package_names = ygg.remove_packages(display_package_names)
        return display_package_names
        # return display_group_names + display_package_names

    def embed_script(self, tarball):
        tarball_content = get_file_content(tarball, 'rb', decode_flag=False)
        tarball_name = os.path.splitext(os.path.splitext(os.path.basename(tarball))[0])[0]
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
        script_str = script_str.replace('{RESULT_NAME}', tarball_name)

        script = Script(script_str, type=KS_SCRIPT_POST, inChroot=True)
        self.ks.handler.scripts.append(script)

    def save_kickstart(self):
        kickstart_data = self.ks.handler.__str__()
        kickstart_data = kickstart_data.replace('%pre', '%%include %s\n\n%%pre\n' % self.temp_file)
        write_to_file(self.kick_start_name, 'wb', kickstart_data)

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
                    log_message("Copying %s to %s failed" % (source_name, target_name))
                    pass

    @staticmethod
    def get_volume_info(filename, first_index, second_index):
        try:
            volume_list = get_file_content(os.path.join(settings.KS_DIR, filename), 'rb', method=True, decode_flag=False)
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
            for key, value in six.iteritems(repositories):
                self.ks.handler.repo.dataList().append(self.ks.handler.RepoData(name=key, baseurl=value.strip()))

    def update_users(self, users):
        if not users:
            return None
        for key, value in users.iteritems():
            uid, gid = value
            self.ks.handler.user.dataList().append(self.ks.handler.UserData(name=key, uid=int(uid), groups=[gid]))

    def get_partition_layout(self, lsblk, vgs, lvdisplay):
        """
        Returns dictionary with partition and realname and size
        :param filename:  filename with partition_layout in /root/preupgrade/kickstart directory
        :return: dictionary with layout
        """
        lsblk_filename = os.path.join(settings.KS_DIR, lsblk)
        try:
            layout = get_file_content(lsblk_filename, 'rb', method=True, decode_flag=False)
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
        pg = PartitionGenerator(layout, vg_info, lv_info)
        pg.generate_partitioning()
        self.part_layout.extend(pg.get_partitioning())

    def update_partitioning(self):
        if self.part_layout is None:
            return

        # Index 1 means size
        script_str = ['echo "# This is partition layout generated by preupg --kickstart command" > %s' % self.temp_file]
        script_str.extend(['echo "%s" >> %s' % (line, self.temp_file) for line in self.part_layout])
        script = Script('\n'.join(script_str), type=KS_SCRIPT_PRE, inChroot=True)
        self.ks.handler.scripts.append(script)

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
        if not self.users:
            return None
        setup_passwd = KickstartGenerator.get_kickstart_users('setup_passwd')
        uidgid = KickstartGenerator.get_kickstart_users('uidgid', splitter='|')
        for user, ids in six.iteritems(self.users):
            if setup_passwd:
                if [x for x in six.iterkeys(setup_passwd) if user in x]:
                    continue
            if uidgid:
                if [x for x in six.iterkeys(uidgid) if user in x]:
                    continue
            kickstart_users[user] = ids.split(':')
        if not kickstart_users:
            return None
        return kickstart_users

    def generate(self):
        if not self.collect_data():
            log_message("Important data are missing for kickstart generation.", level=logging.ERROR)
            return None
        packages = self.output_packages()
        self.ks.handler.packages.add(packages)
        self.update_repositories(self.repos)
        self.update_users(self.filter_kickstart_users())
        self.get_partition_layout('lsblk_list', 'vgs_list', 'lvdisplay')
        self.update_partitioning()
        self.embed_script(self.latest_tarball)
        self.save_kickstart()
        return True


def main():
    kg = KickstartGenerator()
    #print kg.generate()

    # group.packages() -> ['package', ...]
    #import ipdb ; ipdb.set_trace()
    return

if __name__ == '__main__':
    main()
