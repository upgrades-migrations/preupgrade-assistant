# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

import os
from pykickstart.parser import *
from pykickstart.version import makeVersion
from pykickstart.constants import *
from preup.logger import log_message
from preup import settings


class KickstartGenerator(object):
    """
    Generate kickstart using data from provided result
    """
    def __init__(self, result=None):
        #self.yb = yum.YumBase()
        #self.yb.conf.cache = 1
        ## make sure yum has cache
        #self.yb.setCacheDir()
        #self.yb.conf.debuglevel = 0

        self.ks = KickstartGenerator.load_or_default(KickstartGenerator.get_kickstart_path())
        self.result = result

    # def _get_installed_groups(self):
    #     try:
    #         installed, _ = self.yb.doGroupLists()
    #         return installed
    #     except Exception:
    #         return []

    @staticmethod
    def get_kickstart_path():
        return os.path.join(settings.KS_DIR, 'anaconda-ks.cfg')

    @staticmethod
    def load_or_default(system_ks_path):
        """ load system ks or default ks """
        ksparser = KickstartParser(makeVersion())
        try:
            ksparser.readKickstart(system_ks_path)
        except (KickstartError, IOError):
            log_message.info("Can't read system kickstart at %s", system_ks_path)
            try:
                ksparser.readKickstart(settings.KS_TEMPLATE)
            except AttributeError:
                log_message.error("There is no KS_TEMPLATE_POSTSCRIPT specified in settings.py")
            except IOError:
                log_message.error("Can't read kickstart template %s", settings.KS_TEMPLATE)
        return ksparser

    @staticmethod
    def get_package_list_to_install():
        """
        content packages/ReplacedPackages is taking care of packages, which were
        replaced/obsoleted/removed between releases. It produces a file with a list
        of packages which should be installed.
        """

        path = os.path.join(settings.KS_DIR, 'RHRHEL7rpmlist')
        try:
            fp = open(path, 'r')
        except IOError:
            log_message.error("Can't open file with list of packages to be installed: %s", path)
        else:
            lines = fp.readlines()
            fp.close()
        return lines

    def output_packages(self):
        """ outputs %packages section """
        # groups = self._get_installed_groups()
        # group_packages = []
        # for group in groups:
        #     group_packages += group.packages
        # # group names starts with '@' in ks
        # display_group_names = ['@' + group.name for group in groups]
        # display_group_names.sort()

        installed_packages = KickstartGenerator.get_package_list_to_install()

        # we do groups because they change between releases, so dont install packages which are already present in groups
        # display_package_names = [package.name for package in installed_packages if package.name not in group_packages]
        display_package_names = installed_packages[:]
        display_package_names.sort()
        return display_package_names
        # return display_group_names + display_package_names

    def embed_script(self):
        script_str = ''
        try:
            script_path = settings.KS_TEMPLATE_POSTSCRIPT
        except AttributeError:
            log_message.error('KS_TEMPLATE_POSTSCRIPT is not defined in settings.py')
            return
        try:
            script_fd = open(script_path, mode="r")
        except IOError:
            pass
        else:
            script_str = ''.join(script_fd.readlines())
            script_fd.close()
        if not script_str:
            log_message.error("Can't open script template: %s", script_path)
            return

        if self.result and self.request:
            tb_url = self.result.get_tarball_download_url(self.request)
            script_str = script_str.replace('__INSERT_TARBALL_URL__', tb_url)

        script = Script(script_str, type=KS_SCRIPT_POST, inChroot=True)
        self.ks.handler.scripts.append(script)

    def generate(self):
        packages = self.output_packages()
        self.ks.handler.packages.add(packages)
        self.embed_script()
        return self.ks.handler.__str__()


def main():
    kg = KickstartGenerator()
    print kg.generate()

    # group.packages() -> ['package', ...]
    #import ipdb ; ipdb.set_trace()
    return

if __name__ == '__main__':
    main()