# -*- coding: utf-8 -*-

"""
Class creates a kickstart for migration scenario
"""

import os
from pykickstart.parser import *
from pykickstart.data import *
from pykickstart.writer import KickstartWriter
from preup.logger import *
from preup import settings
from preup.utils import write_to_file


class YumGroupManager(object):
    """
    more intelligent dict; enables searching in yum groups
    """
    def __init__(self):
        self.groups = {}

    def add(self, group):
        self.groups[group.name] = group

    def find_match(self, packages):
        """
        is there a group whose packages are subset of argument 'packages'?
        """
        groups = []
        for group in self.groups.itervalues():
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
    """
    class for aggregating packages into yum groups
    """

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
            fd = open(fp, 'r')
            for line in fd.readlines():
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
    """
    Generate kickstart using data from provided result
    """
    def __init__(self, kick_start_name):
        self.ks = KickstartGenerator.load_or_default(KickstartGenerator.get_kickstart_path())
        self.kick_start_name = kick_start_name
        self.ksparser = None

    @staticmethod
    def get_kickstart_path():
        return os.path.join(settings.KS_DIR, 'anaconda-ks.cfg')

    @staticmethod
    def load_or_default(system_ks_path):
        """ load system ks or default ks """
        ksdata = KickstartData()
        kshandlers = KickstartHandlers(ksdata)
        ksparser = KickstartParser(ksdata, kshandlers)
        try:
            ksparser.readKickstart(system_ks_path)
        except (KickstartError, IOError):
            log_message("Can't read system kickstart at %s" % system_ks_path)
            try:
                ksparser.readKickstart(settings.KS_TEMPLATE)
            except AttributeError:
                log_message("There is no KS_TEMPLATE_POSTSCRIPT specified in settings.py")
            except IOError:
                log_message("Can't read kickstart template %s" % settings.KS_TEMPLATE)
        return ksparser

    @staticmethod
    def get_package_list(filename):
        """
        content packages/ReplacedPackages is taking care of packages, which were
        replaced/obsoleted/removed between releases. It produces a file with a list
        of packages which should be installed.
        """

        lines = []
        path = os.path.join(settings.KS_DIR, filename)
        try:
            fp = open(path, 'r')
        except IOError:
            log_message("Can't open file with list of packages to be installed: %s" % path)
        else:
            # Remove newline character from list
            lines = [line.strip() for line in fp.readlines()]
            fp.close()
        return lines

    def output_packages(self):
        """ outputs %packages section """
        installed_packages = KickstartGenerator.get_package_list('RHRHEL7rpmlist')
        removed_packages = KickstartGenerator.get_package_list('RemovedPkg-optional')
        abs_fps = [os.path.join(settings.KS_DIR, fp) for fp in settings.KS_FILES]
        ygg = YumGroupGenerator(installed_packages, removed_packages, *abs_fps)
        display_package_names = ygg.get_list()
        display_package_names = ygg.remove_packages(display_package_names)
        return display_package_names
        # return display_group_names + display_package_names

    def embed_script(self, tb_url):
        script_str = ''
        try:
            script_path = settings.KS_TEMPLATE_POSTSCRIPT
        except AttributeError:
            log_message('KS_TEMPLATE_POSTSCRIPT is not defined in settings.py')
            return
        try:
            script_fd = open(script_path, mode="r")
        except IOError:
            pass
        else:
            script_str = ''.join(script_fd.readlines())
            script_fd.close()
        if not script_str:
            log_message("Can't open script template: %s" % script_path)
            return

        #tb_url = self.result.get_tarball_download_url(self.request)
        #script_str = script_str.replace('__INSERT_TARBALL_URL__', tb_url)

        #script = Script(script_str, type=KS_SCRIPT_POST, inChroot=True)
        #self.ks.handler.scripts.append(script)

    def save_kickstart(self):
        try:
            kswriter = KickstartWriter(self.ks.ksdata)
            outfile = open(self.kick_start_name, 'w')
            outfile.write(kswriter.write())
            outfile.close()
        except IOError, es:
            log_message("Could not save a kickstart %s. " % self.kick_start_name)

    def generate(self):
        packages = self.output_packages()
        for pkg in packages:
            self.ks.addPackages(pkg)
        self.save_kickstart()
        #self.embed_script()
        #return self.ks.handler.__str__()


def main():
    kg = KickstartGenerator()
    print kg.generate()

    # group.packages() -> ['package', ...]
    #import ipdb ; ipdb.set_trace()
    return

if __name__ == '__main__':
    main()