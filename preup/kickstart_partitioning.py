# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

from __future__ import print_function, unicode_literals
import six


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
