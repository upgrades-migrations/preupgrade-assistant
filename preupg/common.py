"""
The class is used for common stuff issues like
generating common logs, coping these common logs
to assessment
"""

from __future__ import unicode_literals
import os
import datetime
import shutil
from distutils import dir_util
from preupg.utils import FileHelper, DirHelper, ProcessHelper
from preupg.utils import SystemIdentification
from preupg.logger import log_message
from preupg import settings


class Common(object):

    """Class handles with common log files"""

    def __init__(self, conf):
        self.conf = conf
        self.cwd = ""
        self.lines = FileHelper.get_file_content(self.conf.common_scripts,
                                                 "rb", True)
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
            DirHelper.check_or_create_temp_dir(com_dir)
        self.cwd = os.getcwd()
        os.chdir(self.get_common_dir())

    def switch_back_dir(self):
        """Function switch back to self.cwd"""
        os.chdir(self.cwd)

    def common_results(self):
        """run common scripts"""
        log_message("Gathering logs used by the Preupgrade Assistant:")
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
                            new_line=False)
                start_time = datetime.datetime.now()
                common_file_path = self.common_logfiles(log_file)
                ProcessHelper.run_subprocess(cmd, output=common_file_path, shell=True)
                end_time = datetime.datetime.now()
                diff = end_time - start_time
                log_message(" %sfinished (time %.2d:%.2ds)" % ('\b' * 8,
                                                               diff.seconds / 60,
                                                               diff.seconds % 60))
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
                                    os.path.join(self.conf.assessment_results_dir,
                                                 "kickstart",
                                                 values[5]))
                else:
                    if os.path.exists(os.path.join(self.conf.assessment_results_dir,
                                                   values[1])):
                        os.remove(values[1])
        except IOError:
            return 0
        else:
            self.switch_back_dir()
            return 1
