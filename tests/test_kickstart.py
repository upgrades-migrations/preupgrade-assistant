
from __future__ import unicode_literals, print_function
import unittest
import os

import base

from preup.kickstart import KickstartGenerator

PREUPGRADE_KS = 'preupgrade.ks'


def get_full_path(file_name):
    return os.path.join(os.getcwd(), 'tests', 'partition_data', file_name)


class TestPartitioning(base.TestCase):

    ks = None

    def setUp(self):
        kickstart_file = get_full_path(PREUPGRADE_KS)
        self.ks = KickstartGenerator(kickstart_file, os.path.join(os.getcwd(), 'tests', 'partition_data'))

    def test_lvm_partitions(self):
        lvm_lsblk = get_full_path('lvm_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part --size=500M --ondisk=vda --fstype="ext4"',
                           'part pv.01 --size 9.5G ',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8.5G --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1G --name=lv_swap']
        self.assertEqual(expected_layout, self.ks.part_layout)

    def test_lvm_crypt_partitions(self):
        lvm_lsblk = get_full_path('lvm_crypt_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part --size=500M --ondisk=vda --fstype="ext4"',
                           'part pv.01 --size 9.5G --encrypted',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8.5G --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1G --name=lv_swap']
        self.assertEqual(expected_layout, self.ks.part_layout)

    """def test_lvm_complicated_partitions(self):
        lvm_lsblk = get_full_path('lvm_complicated_lsblk_list')
        vgs_list = get_full_path('vgs_list_complicated')
        lvdisplay = get_full_path('lvdisplay_complicated')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part --size=500M --ondisk=vda --fstype="ext4"',
                           'part pv.1 --size 9.5G --encrypted',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8.5G --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1G --name=lv_swap']
        self.assertEqual(expected_layout, self.ks.part_layout)
    """

    def tearDown(self):
        pass


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestPartitioning))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
