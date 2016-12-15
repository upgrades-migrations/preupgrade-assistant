
from __future__ import unicode_literals, print_function
import unittest
import os
import tempfile
import shutil

from preupg.kickstart.application import KickstartGenerator
from preupg.kickstart.cli import CLIKickstart
from preupg.kickstart.conf import ConfKickstart, DummyConfKickstart
from preupg import settings

try:
    import base
except ImportError:
    import tests.base as base


def get_full_path(file_name):
    return os.path.join(os.getcwd(), 'tests', 'kickstart_data', file_name)


class TestKickstartPartitioning(base.TestCase):

    kickstart = None
    dir_name = None
    WORKING_DIR = ''
    lsblk_list = 'lsblk_list'
    vgs_list = 'vgs_list'
    lvdisplay = 'lvdisplay'
    firewall_cmd = 'firewall-cmd'
    users = 'Users'
    groups = 'Groups'
    kg = None

    def setUp(self):
        ks_template = settings.KS_TEMPLATE
        self.WORKING_DIR = tempfile.mkdtemp(prefix='preupg')
        if os.path.isdir(self.WORKING_DIR):
            shutil.rmtree(self.WORKING_DIR)
        os.makedirs(self.WORKING_DIR)
        settings.KS_DIR = self.WORKING_DIR
        shutil.copyfile(os.path.join(os.getcwd(), 'data', 'templates',
                                     ks_template),
                        os.path.join(self.WORKING_DIR, ks_template))
        conf = {"y": True}
        dc = DummyConfKickstart(**conf)
        cli_kickstart = CLIKickstart(["--assumeyes"])
        conf = ConfKickstart(cli_kickstart.opts, dc, cli_kickstart)
        self.kg = KickstartGenerator(conf, self.WORKING_DIR,
                                     settings.KS_FILENAME)
        self.kg.collect_data()

    def test_lvm_partitions(self):
        lvm_lsblk = get_full_path('lvm_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        shutil.copyfile(lvm_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        shutil.copyfile(vgs_list, os.path.join(self.WORKING_DIR, self.vgs_list))
        shutil.copyfile(lvdisplay, os.path.join(self.WORKING_DIR, self.lvdisplay))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part /boot --ondisk=vda --size=500',
                           'part pv.01 --size=9000',
                           'volgroup vg_rhel67 --pesize=4096 pv.01',
                           'logvol /  --size=8000 --name=lv_root --vgname=vg_rhel67',
                           'logvol swap  --size=1000 --name=lv_swap --vgname=vg_rhel67']
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_lvm_crypt_partitions(self):
        lvm_lsblk = get_full_path('lvm_crypt_lsblk_list')
        vgs_list = get_full_path('vgs_list')
        lvdisplay = get_full_path('lvdisplay')
        shutil.copyfile(lvm_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        shutil.copyfile(vgs_list, os.path.join(self.WORKING_DIR, self.vgs_list))
        shutil.copyfile(lvdisplay, os.path.join(self.WORKING_DIR, self.lvdisplay))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part /boot --ondisk=vda --size=500',
                           'part pv.01 --size=9000',
                           'volgroup vg_rhel67 --pesize=4096 pv.01',
                           'logvol /  --size=8000 --name=lv_root --vgname=vg_rhel67',
                           'logvol swap  --size=1000 --name=lv_swap --vgname=vg_rhel67']
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_crypt_partitions(self):
        lvm_lsblk = get_full_path('crypt_lsblk_list')
        shutil.copyfile(lvm_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part / --size=3000 --encrypted',
                           'part /boot --ondisk=vda --size=200',
                           'part swap --ondisk=vda --size=2000']
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_raid_crypt_partitions(self):
        raid_lsblk = get_full_path('raid_lsblk_list')
        shutil.copyfile(raid_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part /boot --ondisk=sda --size=200',
                           'part swap --ondisk=sda --size=1000',
                           'part raid.00001 --grow --size=2048',
                           'part raid.00002 --grow --size=2048',
                           'part raid.00003 --grow --size=2048',
                           'part raid.00004 --grow --size=2048',
                           'raid / --device=md1 --level=1 raid.00001 raid.00002',
                           'raid /home --device=md0 --level=0 --encrypted raid.00003 raid.00004'
                           ]
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_raid_second_partitions(self):
        raid_lsblk = get_full_path('raid_lsblk_second_list')
        shutil.copyfile(raid_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part /boot --ondisk=vda --size=1000 ',
                           'part swap --ondisk=vdb --size=1000',
                           'part raid.00001 --grow --size=2048',
                           'part raid.00002 --grow --size=2048',
                           'raid / --device=md0 --level=0 raid.00001 raid.00002',
                           ]
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_native_partitioning(self):
        lsblk_native_lsblk = get_full_path('lsblk_native_list')
        shutil.copyfile(lsblk_native_lsblk, os.path.join(self.WORKING_DIR, self.lsblk_list))
        self.kg.generate()
        expected_layout = ['clearpart --all',
                           'part / --ondisk=vda --size=5000',
                           'part /boot --ondisk=vda --size=200',
                           'part /home --ondisk=vda --size=2000',
                           'part swap --ondisk=vda --size=1000',
                           ]
        for layout in expected_layout:
            self.assertTrue(layout.strip() in self.kg.ks.handler.__str__())

    def test_firewall_rules(self):
        firewall_cmd = get_full_path(self.firewall_cmd)
        shutil.copyfile(firewall_cmd, os.path.join(self.WORKING_DIR, self.firewall_cmd))
        self.kg.generate()
        expected_layout = ['firewall --enabled --service=foo,bar,test']
        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def test_user_and_groups(self):
        files = ['Users', 'Groups', 'setup_passwd', 'uidgid']
        for f in files:
            shutil.copyfile(get_full_path(f), os.path.join(self.WORKING_DIR, f))
        self.kg.generate()
        expected_layout = ['group --name=foobar --gid=500',
                           'group --name=testfoo --gid=506',
                           'group --name=preupg --gid=501',
                           'user --homedir=/home/foobar --name=foobar --shell=/bin/bash --uid=500 --gid=500',
                           'user --homedir=/ --name=testfoo --shell=/sbin/nologin --uid=506 --gid=506',
                           'user --homedir=/home/preupg --name=preupg --shell=/sbin/nologin --uid=501 --gid=501']

        for layout in expected_layout:
            self.assertTrue(layout.strip(), self.kg.ks.handler.__str__())

    def tearDown(self):
        pass


class TestKickstartFirewall(object):

    def setUp(self):
        pass

    def tearDown(self):
        pass


def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestKickstartPartitioning))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=3).run(suite())
