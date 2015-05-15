"""
The class is used for common stuff issues like
generating common logs, coping these common logs
to assessment
"""

from __future__ import unicode_literals
import os
import platform
import datetime
import shutil
from distutils import dir_util
from preup import utils
from preup.utils import run_subprocess
from preup.logger import log_message
from preup import settings


def get_add_on_name(filename, add_on):
    """Function returns the server name with add_on"""
    return filename + "-" + add_on


class Common(object):

    """Class handles with common log files"""

    def __init__(self, conf):
        self.conf = conf
        self.cwd = ""
        self.lines = utils.get_file_content(self.conf.common_script, "rb", method=True)
        self.common_result_dir = ""

    def common_logfiles(self, filename):
        """build path for provided filename"""
        return os.path.join(self.get_common_dir(), filename)

    def get_common_dir(self):
        """Function returns common dir"""
        return os.path.join(self.conf.cache_dir, settings.common_name)

    def switch_dir(self):
        """Switch to current directory"""
        com_dir = self.get_common_dir()
        if not os.path.exists(com_dir):
            utils.check_or_create_temp_dir(com_dir)
        self.cwd = os.getcwd()
        os.chdir(self.get_common_dir())

    def switch_back_dir(self):
        """Function switch back to self.cwd"""
        os.chdir(self.cwd)

    def common_results(self):
        """run common scripts"""
        log_message("Gathering logs used by preupgrade assistant:")
        self.switch_dir()
        try:
            max_length = max(max([len(x.split("=", 4)[3]) for x in self.lines]), len(settings.assessment_text))
            # Log files which will not be updated
            # when RPM database is not changed
            for counter, line in enumerate(self.lines):
                line = line.strip()
                if line.startswith("#"):
                    continue
                cmd, log_file, dummy_bash_value, name, values = line.split("=", 4)
                log_message("%s : %.2d/%d ...running" % (name.ljust(max_length),
                                                         counter+1,
                                                         len(self.lines)),
                            new_line=False, log=False)
                start_time = datetime.datetime.now()
                common_file_path = self.common_logfiles(log_file)
                run_subprocess(cmd, output=common_file_path, shell=True)
                end_time = datetime.datetime.now()
                diff = end_time - start_time
                log_message(" %sfinished (time %.2d:%.2ds)" % ('\b' * 8,
                                                               diff.seconds / 60,
                                                               diff.seconds % 60),
                            log=False)
                # os.chmod(common_file_path, 0640)
            self.switch_back_dir()
        except IOError:
            return 0
        else:
            return 1

    def copy_common_files(self):
        """run common scripts"""
        self.switch_dir()

        try:
            for line in self.lines:
                if line.strip().startswith("#"):
                    continue
                values = line.strip().split("=", 5)
                if values[4] == "YES":
                    shutil.copyfile(values[1],
                                    os.path.join(self.conf.result_dir,
                                                 "kickstart",
                                                 values[5]))
                else:
                    if os.path.exists(os.path.join(self.conf.result_dir,
                                                   values[1])):
                        os.remove(values[1])
        except IOError:
            return 0
        else:
            self.switch_back_dir()
            return 1

    def get_default_name(self, filename):
        """Function returns a full default name need for symlink"""
        return os.path.join(self.common_result_dir, filename)

    def remove_common_symlink(self, filename):
        """Function removes a symlink if it already exists"""
        filename_remove = self.get_default_name(filename)
        if os.path.islink(filename_remove):
            os.unlink(filename_remove)

    def create_common_symlink(self, filename, variant):
        """
        Function removes previous link if exists
        and then creates a new one
        """
        self.remove_common_symlink(filename)
        sym_link_name = filename.replace(variant, 'default')
        os.symlink(os.path.join(self.common_result_dir,
                                platform.machine(),
                                filename),
                   os.path.join(self.common_result_dir, sym_link_name))

    def copy_kickstart_files(self, dir_name, variant):
        """
        Function copies files which are needed by kickstart

        :param source dir_name:
        :return:
        """
        for file_name in settings.KS_FILES:
            target_file = os.path.join(settings.KS_DIR, file_name)
            orig_name = file_name.replace('default', variant)
            source_name = os.path.join(dir_name, platform.machine(), orig_name)
            if not os.path.exists(target_file) and os.path.exists(source_name):
                shutil.copyfile(source_name, target_file)

    def prep_symlinks(self, assessment_dir, scenario=""):
        """Prepare a symlinks for relevant architecture and Server Variant"""
        server_variant = utils.get_variant()
        if server_variant is None:
            return
        self.common_result_dir = os.path.join(assessment_dir, settings.common_name)
        # We need to copy /usr/share/preupgrade/RHEL6_7/common also in case of
        # usage --contents option. Some contents needs a /root/preupgrade/RHEL6_7/common
        # directory
        if self.conf.contents:
            usr_common_name = os.path.join(settings.source_dir, scenario, settings.common_name)
            if os.path.exists(usr_common_name):
                dir_util.copy_tree(usr_common_name, os.path.join(assessment_dir, settings.common_name))
        # We have repositories for i386 architecture but packages are built
        # sometimes as i686 architecture. That's problematic in some cases
        # so we solve this for now by this little hack ugly.
        if (not os.path.exists(os.path.join(self.common_result_dir, 'i686'))
           and os.path.exists(os.path.join(self.common_result_dir, 'i386'))):
            os.symlink(os.path.join(self.common_result_dir, 'i386'),
                       os.path.join(self.common_result_dir, 'i686'))
        add_ons = utils.get_addon_variant()
        dir_name = os.path.join(self.common_result_dir,
                                platform.machine())
        if not os.path.exists(dir_name):
            return
        server_variant_files = [files for files in os.listdir(dir_name) if files.startswith(server_variant) or files.startswith("Common")]
        self.copy_kickstart_files(self.common_result_dir, server_variant)
        for files in server_variant_files:
            # First create a default links to "ServerVariant_"
            if files.startswith(server_variant+"_"):
                self.create_common_symlink(files, server_variant)
            elif files.startswith("Common"):
                self.create_common_symlink(files, "Common")
            else:
                # Now create a symlink for ServerVariant-AddOn_
                for add_on in add_ons:
                    if not files.startswith(get_add_on_name(server_variant, add_on)+"_"):
                        continue
                    self.create_common_symlink(files, server_variant)
