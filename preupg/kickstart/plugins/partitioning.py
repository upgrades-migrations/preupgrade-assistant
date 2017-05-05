# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

import os

from pykickstart.constants import CLEARPART_TYPE_ALL
from preupg.kickstart.application import BaseKickstart
from preupg.utils import FileHelper
from preupg.logger import log_message, logging
from preupg import settings


class PartitionGenerator(BaseKickstart):
    """Generate partition layout"""
    def __init__(self, handler):
        self.part_layout = None
        self.layout = None
        self.vg_info = None
        self.lvdisplay = None
        self.raid_devices = {}
        self.vol_group = {}
        self.logvol = {}
        self.part_dict = {}
        self.handler = handler
        self.parts = []
        self.vg_list = []
        self.lv_list = []
        self.raid_list = []

    def generate_partitioning(self):
        pv_name = ""
        index_pv = 1
        crypt = ""
        if self.layout is None:
            return None
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
            if device_type == 'disk' or device_type == 'crypt' or \
                    device_type == 'rom':
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
                    if pv_name not in self.part_dict:
                        self.part_dict[pv_name] = {}
                    self.part_dict[pv_name]['size'] = size
                    self.part_dict[pv_name]['crypt'] = crypt
                    crypt = ""
                    index_pv += 1
                    continue
                else:
                    device = ''.join([x for x in device if not x.isdigit()])
                    if mount not in self.part_dict:
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
                if mount not in self.raid_devices:
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
                try:
                    vg_name = [x for x in iter(self.vg_info.keys())
                               if device.startswith(x)][0]
                except IndexError:
                    return
                # Get volume group name
                if vg_name not in self.vol_group:
                    self.vol_group[vg_name] = {}
                self.vol_group[vg_name]['pesize'] = 4096
                self.vol_group[vg_name]['pv_name'] = pv_name
                if self.lvdisplay is None or not self.lvdisplay:
                    continue
                lv_name = [x for x in iter(self.lvdisplay.keys())
                           if x in device][0]
                if mount not in self.logvol:
                    self.logvol[mount] = {}
                self.logvol[mount]['vgname'] = vg_name
                self.logvol[mount]['size'] = size
                self.logvol[mount]['lv_name'] = lv_name

    def _get_part_devices(self):
        for key, value in sorted(iter(self.part_dict.items())):
            if value['crypt'] == "":
                try:
                    self.parts.append(self.handler.PartData(
                        size=value['size'], mountpoint=key,
                        disk=value['device'])
                    )
                except KeyError:
                    self.parts.append(self.handler.PartData(size=value['size'],
                                                            mountpoint=key))
            else:
                self.parts.append(self.handler.PartData(
                    size=value['size'], mountpoint=key,
                    encrypted=value['crypt'])
                )

    def _get_logvol_device(self):
        for key, value in sorted(iter(self.logvol.items())):
            self.lv_list.append(self.handler.LogVolData(
                name=value['lv_name'], vgname=value['vgname'],
                size=value['size'], mountpoint=key)
            )

    def _get_vg_device(self):
        for key, value in iter(self.vol_group.items()):
            pv_name = value['pv_name']
            self.vg_list.append(self.handler.VolGroupData(
                vgname=key, physvols=[pv_name], pesize=value['pesize'])
            )

    def _get_raid_devices(self):
        for key, value in iter(self.raid_devices.items()):
            level = value['level']
            members = []
            for index in value['raid_devices']:
                member = "raid.%.5d" % int(index)
                members.append(member)
                self.parts.append(self.handler.PartData(grow=True, size=2048,
                                                        mountpoint=member))
            device = "md%s" % level
            self.raid_list.append(self.handler.RaidData(
                level=level, mountpoint=key, device=device,
                members=members, encrypted=value['crypt'])
            )

    @staticmethod
    def get_volume_info(filename, first_index, second_index):
        try:
            volume_list = FileHelper.get_file_content(filename, 'rb',
                                                      method=True,
                                                      decode_flag=False)
        except IOError:
            log_message("The %s file is missing. The partitioning layout might"
                        " not be complete." % filename, level=logging.WARNING)
            return None
        volume_info = {}
        for line in volume_list:
            fields = line.strip().split(':')
            volume_info[fields[first_index]] = fields[second_index]
        return volume_info

    def get_partition_layout(self, lsblk, vgs, lvdisplay):
        lsblk_filename = os.path.join(settings.KS_DIR, lsblk)
        try:
            self.layout = FileHelper.get_file_content(lsblk_filename, 'rb',
                                                      method=True,
                                                      decode_flag=False)
        except IOError:
            log_message("The %s file was not generated by the module. "
                        "Kickstart does not contain the partitioning layout"
                        % lsblk_filename)
            self.part_layout = None
            return None
        if vgs is not None:
            self.vg_info = PartitionGenerator.get_volume_info(
                os.path.join(settings.KS_DIR, vgs), 0, 5
            )
        if lvdisplay is not None:
            self.lvdisplay = PartitionGenerator.get_volume_info(
                os.path.join(settings.KS_DIR, lvdisplay), 0, 1
            )

    def get_partitioning(self):
        self.handler.clearpart.type = CLEARPART_TYPE_ALL
        self._get_part_devices()
        self._get_vg_device()
        self._get_logvol_device()
        self._get_raid_devices()
        self.handler.partition(partitions=self.parts)
        self.handler.logvol(lvList=self.lv_list)
        self.handler.volgroup(vgList=self.vg_list)
        self.handler.raid(raidList=self.raid_list)

    def run_module(self, *args, **kwargs):
        self.get_partition_layout('lsblk_list', 'vgs_list', 'lvdisplay')
        self.generate_partitioning()
        self.get_partitioning()
