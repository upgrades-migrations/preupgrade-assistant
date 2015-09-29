
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
        kickstart_file = 'preupgrade.ks'
        self.ks = KickstartGenerator(os.path.join(os.getcwd(), 'tests', 'partition_data'), kickstart_file)

    def test_lvm_partitions(self):
        lvm_lsblk = get_full_path('lvm_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part /boot --size=500 --ondisk=vda',
                           'part pv.01 --size=9000',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8000 --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1000 --name=lv_swap']
        self.assertEqual(expected_layout, self.ks.part_layout)

    def test_lvm_crypt_partitions(self):
        lvm_lsblk = get_full_path('lvm_crypt_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part /boot --size=500 --ondisk=vda',
                           'part pv.01 --size=9000 --encrypted',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8000 --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1000 --name=lv_swap']
        self.assertEqual(expected_layout, self.ks.part_layout)

    def test_crypt_partitions(self):
        lvm_lsblk = get_full_path('crypt_lsblk_list')
        vgs_list = None
        lvdisplay = None
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part / --size=3000 --encrypted',
                           'part /boot --size=200 --ondisk=vda',
                           'part swap --size=2000 --ondisk=vda']
        self.assertEqual(expected_layout, self.ks.part_layout)

    def test_raid_crypt_partitions(self):
        raid_lsblk = get_full_path('raid_lsblk_list')
        self.ks.get_partition_layout(raid_lsblk, None, None)
        expected_layout = ['clearpart --all',
                           'part /boot --size=200 --ondisk=sda',
                           'part swap --size=1000 --ondisk=sda',
                           'part raid.01 --grow --size=2048',
                           'part raid.02 --grow --size=2048',
                           'raid / --level=1 --device=md1 raid.01 raid.02',
                           'part raid.03 --grow --size=2048',
                           'part raid.04 --grow --size=2048',
                           'raid /home --level=0 --device=md0 raid.03 raid.04 --encrypted --passphrase='
                           ]
        self.assertEqual(expected_layout, self.ks.part_layout)

    def test_raid_second_partitions(self):
        raid_lsblk = get_full_path('raid_lsblk_second_list')
        self.ks.get_partition_layout(raid_lsblk, None, None)
        expected_layout = ['clearpart --all',
                           'part /boot --size=1000 --ondisk=vda',
                           'part swap --size=1000 --ondisk=vdb',
                           'part raid.01 --grow --size=2048',
                           'part raid.02 --grow --size=2048',
                           'raid / --level=0 --device=md0 raid.01 raid.02',
                           ]
        self.assertListEqual(self.ks.part_layout, expected_layout)

    def test_native_partitioning(self):
        raid_lsblk = get_full_path('lsblk_native_list')
        self.ks.get_partition_layout(raid_lsblk, None, None)
        expected_layout = ['clearpart --all',
                           'part / --size=5000 --ondisk=vda',
                           'part /boot --size=200 --ondisk=vda',
                           'part /home --size=2000 --ondisk=vda',
                           'part swap --size=1000 --ondisk=vda',
                           ]
        self.assertListEqual(self.ks.part_layout, expected_layout)

    """def test_lvm_complicated_partitions(self):
        lvm_lsblk = get_full_path('lvm_complicated_lsblk_list')
        vgs_list = get_full_path('vgs_list_complicated')
        lvdisplay = get_full_path('lvdisplay_complicated')
        self.ks.get_partition_layout(lvm_lsblk, vgs_list, lvdisplay)
        expected_layout = ['clearpart --all',
                           'part --size=500M --ondisk=vda',
                           'part pv.1 --size 9.5G --encrypted',
                           'volgroup vg_rhel67 pv.01 --pesize=4096',
                           'logvol / --vgname=vg_rhel67 --size=8000 --name=lv_root',
                           'logvol swap --vgname=vg_rhel67 --size=1000 --name=lv_swap']
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
