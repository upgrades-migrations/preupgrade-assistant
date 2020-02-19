# -*- coding: utf-8 -*-
"""
The application module serves for running oscap binary and reporting results
to UI.
"""

from __future__ import unicode_literals, print_function
import shutil
import datetime
import os
import subprocess
import sys
import logging
from distutils import dir_util

try:
    from xmlrpclib import Fault
except ImportError:
    from xmlrpc.client import Fault

from preupg import xml_manager, settings, exception
from preupg.common import Common
from preupg.settings import ReturnValues
from preupg.scanning import ScanProgress, ScanningHelper
from preupg.utils import (FileHelper, ProcessHelper, DirHelper, OpenSCAPHelper,
                          MessageHelper, TarballHelper, SystemIdentification,
                          PostupgradeHelper, ConfigHelper, ConfigFilesHelper,
                          ModuleSetUtils)
from preupg.xccdf import XccdfHelper
from preupg.logger import log_message, LoggerHelper, logger, logger_report
from preupg.logger import logger_debug
from preupg.report_parser import ReportParser
from preupg.kickstart.application import KickstartGenerator
from preupg.xmlgen.compose import XCCDFCompose
from preupg.version import VERSION


def fault_repr(self):
    """Monkey patching Fault's repr method to interpret newlines."""
    log_message(self.faultString)
    return "<Fault %s: %s>" % (self.faultCode, self.faultString)


Fault.__repr__ = fault_repr


def get_installed_module_sets(source_dir):
    """Return a dictionary of installed module sets within a directory. Format
    of the dictionary:
      {<module set root dir name>: <all xccdf xml full path>}
    """
    module_sets = {}
    is_dir = lambda x: os.path.isdir(os.path.join(source_dir, x))
    dirs = os.listdir(source_dir)
    for module_set_root_dir in filter(is_dir, dirs):
        all_xccdf_xml_path = os.path.join(
            source_dir, module_set_root_dir, settings.all_xccdf_xml_filename)
        if os.path.exists(all_xccdf_xml_path):
            logger_debug.info('%s', module_set_root_dir)
            module_sets[module_set_root_dir] = all_xccdf_xml_path
    return module_sets


def show_message(message):
    """
    Prints message out on stdout message (kind of yes/no) and return answer.

    Return values are:
    Return True on accept (y/yes). Otherwise returns False
    """
    accept = ['y', 'yes']
    choice = MessageHelper.get_message(title=message, prompt='[Y/n]')
    if choice.lower() in accept:
        return True
    else:
        return False


class Application(object):

    """Class for oscap binary and reporting results to UI"""

    def __init__(self, conf):
        """conf is preupg.conf.Conf object, contains configuration"""
        self.conf = conf
        self.all_xccdf_xml_path = ""
        self.all_xccdf_xml_copy_path = ""
        self.module_set_dirname = ""
        self.module_set_path = ""
        self.module_set_copy_path = ""
        self.result_file = ""
        self.xml_mgr = None
        self.scanning_progress = None
        self.report_parser = None
        self.text_convertor = ""
        self.common = None
        self._devel_mode = 0
        self._dist_mode = None
        self.report_log_file = None
        self.debug_log_file = None
        settings.profile = self.conf.profile
        if self.conf.debug is None:
            LoggerHelper.add_stream_handler(logger, logging.INFO)
        else:
            LoggerHelper.add_stream_handler(logger, logging.DEBUG)
        self.openscap_helper = None
        self._add_report_log_file()
        self._add_debug_log_file()
        self.tar_ball_name = None
        self._set_old_report_style()

    def _add_report_log_file(self):
        """
        Add the special report log file
        :return:
        """
        try:
            LoggerHelper.add_file_handler(
                logger_report, settings.preupg_report_log,
                formatter=logging.Formatter(
                    "%(asctime)s %(filename)s:%(lineno)s %(funcName)s:"
                    " %(message)s"),
                level=logging.DEBUG
            )
        except (IOError, OSError):
            logger.warning("Can not create report log '%s'",
                           settings.preupg_report_log)
        else:
            self.report_log_file = settings.preupg_report_log

    def _add_debug_log_file(self):
        """
        Add the special report log file
        :return:
        """
        try:
            LoggerHelper.add_file_handler(
                logger_debug, settings.preupg_log,
                formatter=logging.Formatter(
                    "%(asctime)s %(levelname)s\t%(filename)s"
                    ":%(lineno)s %(funcName)s: %(message)s"),
                level=logging.DEBUG
            )
        except (IOError, OSError):
            logger.warning("Can not create debug log '%s'",
                           settings.preupg_log)
        else:
            self.debug_log_file = settings.preupg_log

    def _set_old_report_style(self):
        """
        Choose which HTML report style should be used.

        Set self.old_report_style to True when it is required from commandline
        or older version of OpenSCAP has been detected.
        """
        if self.conf.old_report_style:
            self.old_report_style = True
        elif OpenSCAPHelper.is_oscap_equal_or_greater(1, 2, 7) is False:
            # in case that OpenSCAP version is lower then 1.2.7, fallback
            # to the old (simple) report style.
            log_message("Generating simply styled report due to the "
                        "limitations of the installed OpenSCAP")
            self.old_report_style = True
        else:
            self.old_report_style = False

    def get_postupgrade_dir(self):
        """Function returns postupgrade dir"""
        return os.path.join(self.conf.assessment_results_dir,
                            settings.postupgrade_dir)

    def upload_results(self):
        """upload tarball with results to frontend"""
        import xmlrpclib
        import socket
        url = ""
        if self.conf.upload is True:
            # lets try default configuration
            log_message('Specify the server where to upload the results.')
            log_message(settings.ui_command.format(self.conf.results))
            return False
        else:
            if self.conf.upload[-1] == '/':
                url = self.conf.upload
            else:
                url = self.conf.upload + '/'
        try:
            proxy = xmlrpclib.ServerProxy(url)
            proxy.submit.ping()
        except Exception as ex:
            message = 'Can\'t connect to preupgrade assistant WEB-UI at %s.' \
                      '\n\nPlease ensure that package' \
                      ' preupgrade-assistant-ui has been installed on target' \
                      ' system and firewall is set up ' \
                      'to allow connections on port 8099.' % url
            log_message(message)
            log_message(ex.__str__())
            return False

        if not self.conf.results:
            tarball_results = TarballHelper.get_latest_tarball(
                settings.tarball_result_dir)
        else:
            tarball_results = self.conf.results
        if tarball_results is None or not os.path.exists(tarball_results):
            log_message("Can't determine what tarball to upload to the UI.",
                        level=logging.ERROR)
            return False
        file_content = FileHelper.get_file_content(tarball_results, 'rb',
                                                   False, False)

        binary = xmlrpclib.Binary(file_content)
        host = socket.gethostname()
        response = proxy.submit.submit_new({
            'data': binary,
            'host': host,
        })
        try:
            status = response['status']
        except KeyError:
            log_message('Invalid response from the server.')
            log_message("Invalid response from the server: %s"
                        % response, level=logging.ERROR)
            return False
        else:
            if status == 'OK':
                try:
                    url = response['url']
                except KeyError:
                    log_message('The report submitted successfully.')
                else:
                    log_message('The report submitted successfully. You can inspect it at %s.' % url)
            else:
                try:
                    message = response['message']
                    log_message('The report not submitted. The server returned a message: ', message)
                    log_message("The report status: %s (%s)" % (status, message), level=logging.ERROR)
                except KeyError:
                    log_message('The report not submitted. The server returned a status: ', status)
                    log_message("The report status: %s" % status, level=logging.ERROR)
                return False
        return True

    def prepare_scan_directories(self):
        """Used for prepartion of directories used during scan functionality"""
        dirs = [self.conf.assessment_results_dir, settings.tarball_result_dir]
        dirs.extend(os.path.join(self.conf.assessment_results_dir, x) for x in settings.preupgrade_dirs)
        if self.conf.temp_dir:
            dirs.append(self.conf.temp_dir)
        for dir_name in dirs:
            DirHelper.check_or_create_temp_dir(dir_name)

        # Copy README files into assessment result directory so the user has
        # them easily available
        for orig_filename, dest_filename in settings.readme_files.items():
            shutil.copyfile(os.path.join(settings.DOC_DIR, orig_filename),
                            os.path.join(settings.assessment_results_dir,
                                         dest_filename))

    def get_total_check(self):
        """Returns a total check"""
        return self.report_parser.get_number_checks()

    def run_scan_process(self):
        """Function scans the source system"""
        self.xml_mgr = xml_manager.XmlManager(self.conf.assessment_results_dir,
                                              self.module_set_copy_path
                                              )

        self.report_parser.add_global_tags(self.conf.assessment_results_dir,
                                           self.rename_custom_module_set(
                                               self.module_set_dirname),
                                           self.conf.mode,
                                           self._devel_mode,
                                           self._dist_mode)

        self.report_parser.modify_result_path(self.conf.assessment_results_dir,
                                              self.rename_custom_module_set(
                                                  self.module_set_dirname),
                                              self.conf.mode)
        # Execute assessment
        self.scanning_progress = ScanProgress(self.get_total_check(), self.conf.debug)
        self.scanning_progress.set_names(self.report_parser.get_name_of_checks())
        log_message('%s:' % settings.assessment_text, new_line=True)
        log_message('%.3d/%.3d ...running (%s)' % (
                    1,
                    self.get_total_check(),
                    self.scanning_progress.get_full_name(0)),
                    new_line=False
                    )
        start_time = datetime.datetime.now()
        self.scanning_progress.time = start_time
        self.run_scan(function=self.scanning_progress.show_progress)
        end_time = datetime.datetime.now()
        diff = end_time - start_time
        log_message(
            "The assessment finished (time %.2d:%.2ds)" % (diff.seconds / 60,
                                                           diff.seconds % 60)
        )

    def run_scan(self, function=None):
        """
        The function is used for either scanning system or
        for applying changes on the target system
        """
        cmd = self.openscap_helper.build_command()
        logger_debug.debug('running_command: %s', cmd)
        return ProcessHelper.run_subprocess(cmd, print_output=False, function=function)

    def clean_preupgrade_environment(self):
        """
        Function cleans files created by preupgrade-assistant

        :return:
        """
        force_directories = [self.conf.assessment_results_dir]
        delete_directories = [settings.tarball_result_dir,
                              settings.cache_dir,
                              settings.log_dir]
        for dir_name in force_directories:
            if os.path.isdir(dir_name):
                shutil.rmtree(dir_name)
        for dir_name in delete_directories:
            for root, dirs, files in os.walk(dir_name, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    shutil.rmtree(os.path.join(root, name))

    def clean_scan(self):
        """
        The function remove symlink /root/preupgrade from older versions
        Also it removes directory /root/preupgrade because of new assessment.
        """
        if os.path.islink(self.conf.assessment_results_dir):
            os.unlink(self.conf.assessment_results_dir)
        if os.path.isdir(self.conf.assessment_results_dir):
            shutil.rmtree(self.conf.assessment_results_dir)

    def prepare_xml_for_html(self):
        """The function prepares a XML file for HTML creation"""
        # Reload XML file
        self.report_parser.reload_xml(self.openscap_helper.get_default_xml_result_path())
        # strip whitespaces on start and end of stdout/stderr from modules
        # inside the result.xml file
        self.report_parser.strip_whitespaces()
        # Replace fail in case of slight and medium risks with needs_inspection
        self.report_parser.replace_inplace_risk(scanning_results=self.scanning_progress)
        if not self.conf.debug:
            self.report_parser.remove_debug_info()
        self.report_parser.reload_xml(self.openscap_helper.get_default_xml_result_path())
        self.report_parser.update_check_description()
        xml_report = self.openscap_helper.get_default_xml_result_path()
        if self.old_report_style:
            ReportParser.write_xccdf_version(xml_report, direction=True)

    def generate_html_or_text(self):
        self.generate_html()
        if self.conf.text:
            ProcessHelper.run_subprocess(self.get_cmd_convertor(), print_output=False, shell=True)

    def generate_html(self):
        """Convert XML to HTML"""
        xml_report = self.openscap_helper.get_default_xml_result_path()
        html_report = self.openscap_helper.get_default_html_result_path()
        self.openscap_helper.run_generate(xml_report,
                                          html_report,
                                          old_style=self.old_report_style)
        self.xml_mgr.update_report(html_report)

    def update_xml_after_html_generated(self):
        xml_report = self.openscap_helper.get_default_xml_result_path()
        self.xml_mgr.update_report(xml_report)
        if self.old_report_style:
            # Revert change to the XML XCCDF namespace which would break preupg-diff
            ReportParser.write_xccdf_version(xml_report)

    def copy_postupgrade_files(self):
        """
        Function copies postupgrade scripts and creates hash postupgrade file.
        """
        # Copy postupgrade.d special files
        PostupgradeHelper.special_postupgrade_scripts(self.conf.assessment_results_dir)
        PostupgradeHelper.hash_postupgrade_file(self.conf.verbose, self.get_postupgrade_dir())

    def get_cmd_convertor(self):
        """Function returns cmd with text convertor string"""
        cmd = settings.text_converters[self.text_convertor].format(
            self.text_convertor,
            self.openscap_helper.get_default_html_result_path(),
            self.openscap_helper.get_default_txt_result_path()
        )
        return cmd

    def rename_custom_module_set(self, module_set_dirname):
        if self.conf.contents:
            module_set_dirname = module_set_dirname.replace('-results', '')
        return module_set_dirname

    def prepare_scan_system(self):
        """
        Prepare system for scan.

        In case the result of previous assessment is detected, remove it
        and prepare new directory structure that will be used for next scan.
        Additionaly process scripts generating common data about the current
        system, generate final XCCDF compose from the original set of modules
        identified for run and in the end process initial script of modules to
        complete expected environment for the scan.
        """
        # First of all we need to delete the older one assessment
        self.clean_scan()
        self.prepare_scan_directories()
        self.common = Common(self.conf)
        if not self.conf.skip_common:
            if not self.common.common_results():
                return ReturnValues.SCRIPT_TXT_MISSING

        # Generate final XCCDF compose under self.module_set_copy_path
        xccdf_compose = XCCDFCompose(
            self.module_set_path, self.module_set_copy_path)
        ret_val = xccdf_compose.generate_xml()
        if ret_val != 0:
            return ret_val
        self.run_init()
        return 0

    def run_init(self):
        """
        Run module set's init script if exists

        If module set provides executable called 'init', run it.   Standard
        output is ignored.  If either exit status is non-zero or error is
        printed, raise ModuleSetInitError.

        Note that exported environment variables need to be reviewed; current
        set is purely to make previous solution work and prevent regression.
        """
        scenario = self.rename_custom_module_set(self.module_set_dirname)
        init = os.path.join(self.conf.source_dir, scenario, 'init')
        if os.access(init, os.F_OK):
            init_vars = {
                'PREUPGM_INIT_ASSESSMENT_DIR': self.module_set_copy_path,
                'PREUPGM_INIT_SCENARIO': scenario,
                'PREUPGM_INIT_DST_ARCH': self.conf.dst_arch if self.conf.dst_arch else "",
                'PREUPGM_INIT_CONTENTS': self.conf.contents if self.conf.contents else "",
            }
            logger_debug.debug("calling module init script with: %r" % init_vars)
            init_env = os.environ.copy()
            init_env.update(init_vars)
            try:
                p = subprocess.Popen(
                    [init],
                    env=init_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                out, err = p.communicate()
            except OSError as e:
                raise exception.ModuleSetFormatError("init script failed to execute", init, e)
            if p.returncode or err.strip():
                raise exception.ModuleSetInitError(p.returncode, err)

    @staticmethod
    def copy_preupgrade_scripts(assessment_dir):
        # Copy preupgrade-scripts directory from scenarvirtuio
        preupg_scripts = os.path.join(assessment_dir,
                                      settings.preupgrade_scripts_dir)
        if os.path.exists(preupg_scripts):
            dir_util.copy_tree(preupg_scripts,
                               settings.preupgrade_scripts_path)

    def scan_system(self):
        """The function is used for scanning system with all steps."""
        self._set_devel_mode()
        if not self.is_module_set_valid():
            return ReturnValues.SCENARIO
        ret_val = self.prepare_scan_system()
        if ret_val != 0:
            return ret_val
        # Update source XML file in temporary directory
        self.openscap_helper.update_variables(self.conf.assessment_results_dir,
                                              self.conf.result_prefix,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.all_xccdf_xml_copy_path)
        try:
            self.report_parser = ReportParser(self.all_xccdf_xml_copy_path)
        except IOError:
            log_message("Error: Unable to open {0}."
                        .format(self.all_xccdf_xml_copy_path))
            return ReturnValues.SCENARIO
        if self.conf.mode:
            lines = [i.rstrip() for i in
                     FileHelper.get_file_content(
                         os.path.join(self.module_set_copy_path,
                                      self.conf.mode),
                         'rb', method=True)]
            self.report_parser.select_rules(lines)
        if self.conf.select_rules:
            lines = [i.strip() for i in self.conf.select_rules.split(',')]
            unknown_rules = self.report_parser.check_rules(lines)
            if unknown_rules:
                log_message(settings.unknown_rules % '\n'.join(unknown_rules))
            self.report_parser.select_rules(lines)
        self.run_scan_process()
        main_report = self.scanning_progress.get_output_data()
        self.prepare_xml_for_html()
        self.generate_html_or_text()
        self.update_xml_after_html_generated()
        self.copy_postupgrade_files()
        self.copy_preupgrade_scripts(self.module_set_copy_path)
        ConfigFilesHelper.copy_modified_config_files(
            settings.assessment_results_dir)

        # It prints out result in table format
        ScanningHelper.format_rules_to_table(main_report, "main contents")

        self.tar_ball_name = TarballHelper.tarball_result_dir(self.conf.tarball_name, self.conf.verbose)
        log_message("The tarball with results is stored in '%s' ." % self.tar_ball_name)
        log_message("The latest assessment is stored in the '%s' directory." % self.conf.assessment_results_dir)
        # pack all configuration files to tarball
        return 0

    def is_module_set_valid(self):
        if self.module_set_dirname is None:
            log_message('Invalid scenario: %s' % self.module_set_path)
            return False
        if not os.path.isdir(self.module_set_path):
            log_message('Invalid scenario: %s' % self.module_set_path,
                        level=logging.ERROR)
            return False
        # Validate properties.ini file in module set dir
        try:
            ModuleSetUtils.get_module_set_os_versions(self.module_set_path)
        except EnvironmentError as err:
            log_message(str(err), level=logging.ERROR)
            return False
        return True

    def summary_report(self, tarball_path):
        """Function prints a summary report"""
        command = settings.ui_command.format(tarball_path)
        if self.conf.text:
            path = self.openscap_helper.get_default_txt_result_path()
        else:
            path = self.openscap_helper.get_default_html_result_path()

        report_dict = {
            0: settings.risks_found_warning.format(path),
            1: settings.risks_found_warning.format(path),
            2: 'We have found some critical issues. In-place upgrade or migration is not advised.\n' +
               "Read the file {0} for more details.".format(path),
            3: 'We have found some error issues. In-place upgrade or migration is not advised.\n' +
               "Read the file {0} for more details.".format(path)
        }
        report_return_value = XccdfHelper.check_inplace_risk(
            self.openscap_helper.get_default_xml_result_path(),
            0)
        try:
            if report_dict[int(report_return_value)]:
                log_message('Summary information:')
                log_message(report_dict[int(report_return_value)])
        except KeyError:
            # We do not want to print anything in case of testing contents
            pass
        if not self.conf.mode or self.conf.mode == "upgrade":
            # User either has not specied mode (upgrade and migration both
            # together by default) or has chosen upgrade only = print warning
            # to backup the system before doing the in-place upgrade
            log_message(settings.upgrade_backup_warning)
        log_message("Upload results to UI by the command:\ne.g. {0} .".format(command))
        return report_return_value

    def _set_devel_mode(self):
        # Check for devel_mode
        if os.path.exists(settings.DEVEL_MODE):
            self._devel_mode = 1
            self._dist_mode = ConfigHelper.get_preupg_config_file(
                settings.PREUPG_CONFIG_FILE, 'dist_mode', section="devel-mode")
        else:
            self._devel_mode = 0

    def get_default_module_set_dirname(self):
        available_module_set_dirs = get_installed_module_sets(
            self.conf.source_dir)
        if not available_module_set_dirs:
            log_message("No modules found in the default directory (%s).\n"
                        " Either install a package with modules or use"
                        " -c option for custom created modules."
                        % settings.source_dir)
            return None
        if len(available_module_set_dirs) > 1:
            log_message("More than one module set is detected in the default"
                        " directory (%s)." % settings.source_dir)
            log_message("Available module sets: \n%s"
                        % '\n'.join(available_module_set_dirs))
            log_message("Use option -s to specify which module set should be"
                        " used.")
            return None
        return available_module_set_dirs.keys()[0]

    def determine_module_set_location(self):
        """Get module set path, directory name and path to the all_xccdf.xml"""
        if not self.conf.contents:  # was the --contents CLI option used?
            if not self.conf.scan:  # and what about the --scan option?
                self.module_set_dirname = self.get_default_module_set_dirname()
                if not self.module_set_dirname:
                    return ReturnValues.SCENARIO
            else:
                self.module_set_dirname = self.conf.scan
            self.module_set_path = os.path.join(self.conf.source_dir,
                                                self.module_set_dirname)
            if not os.path.isdir(self.module_set_path):
                log_message("Module set '%s' is not installed.\nFor a list"
                            " of installed module sets, use -l option."
                            % self.module_set_dirname, level=logging.ERROR)
                return ReturnValues.SCENARIO
            self.all_xccdf_xml_path = os.path.join(
                self.module_set_path, settings.all_xccdf_xml_filename)
        else:
            self.all_xccdf_xml_path = os.path.abspath(self.conf.contents)
            self.module_set_path = os.path.dirname(self.all_xccdf_xml_path)
            self.module_set_dirname = os.path.basename(self.module_set_path)
            if not self.module_set_dirname:
                log_message("Unable to determine a module set directory name.",
                            level=logging.ERROR)
                log_message("The directory name needs to be in format"
                            " 'RHELx_y' for upgrades from RHEL x to RHEL y.",
                            level=logging.ERROR)
                return ReturnValues.SCENARIO
        if not os.path.isfile(self.all_xccdf_xml_path):
            log_message("'%s' does not exist." % self.all_xccdf_xml_path,
                        level=logging.ERROR)
            return ReturnValues.SCENARIO

    def determine_module_set_copy_location(self):
        """The module set to be used for the system assessment will needs to be
        copied into the system assessment working directory. Determine the
        location of the copied module set.
        """
        self.module_set_copy_path = os.path.join(
            settings.assessment_results_dir,
            self.rename_custom_module_set(self.module_set_dirname))
        self.all_xccdf_xml_copy_path = os.path.join(
            self.module_set_copy_path, settings.all_xccdf_xml_filename)

    @staticmethod
    def is_installed_oscap_ok():
        """Check whether expected openscap rpms are installed."""
        class GetCmdStdout():
            def __init__(self):
                self.stdout_lines = []

            def __call__(self, line):
                if line.strip():
                    self.stdout_lines.append(line.strip())

        if not os.path.exists(settings.openscap_binary):
            log_message("Oscap with SCE enabled is not installed")
            return False
        if not os.access(settings.openscap_binary, os.X_OK):
            log_message("Oscap with SCE %s is not executable"
                        % settings.openscap_binary)
            return False
        # that's generic problem that could be on various rpm-based systems
        url = "https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html-single/6.10_release_notes/index#BZ1804691"
        for pkg in settings.openscap_rpms:
            cmd = ["rpm", "-q", pkg, "--qf", "%{ARCH}\n"]
            cmdout = GetCmdStdout()
            ProcessHelper.run_subprocess(cmd, function=cmdout)
            if SystemIdentification.get_arch() not in cmdout.stdout_lines:
                log_message("The %s rpm is not installed for the"
                            " %s architecture. This usually ends in a broken"
                            " state in which all the Preupgrade Assistant modules"
                            " are skipped (notchecked state). Please, install"
                            " packages related for your architecture. See %s"
                            " for more info."
                            % (pkg, SystemIdentification.get_arch(), url))
                return False
        return True

    def run(self):
        """run analysis"""
        version_msg = "Preupgrade Assistant version: %s" % VERSION
        if self.conf.version:
            print (version_msg)
            return 0

        logger_debug.debug(version_msg)
        if self.conf.list_contents_set:
            for dir_name, dummy_content in iter(get_installed_module_sets(
                    self.conf.source_dir).items()):
                log_message("%s" % dir_name)
            return 0

        if self.conf.riskcheck:
            result_xml_path = os.path.join(settings.assessment_results_dir,
                                           settings.xml_result_name)
            if not os.path.exists(result_xml_path):
                log_message("System assessment needs to be performed first.")
                return ReturnValues.PREUPG_BEFORE_RISKCHECK
            return XccdfHelper.check_inplace_risk(result_xml_path,
                                                  self.conf.verbose)

        if self.conf.upload and self.conf.results:
            if not self.upload_results():
                return ReturnValues.SEND_REPORT_TO_UI
            return 0

        if self.conf.cleanup:
            if not self.executed_under_root():
                return ReturnValues.ROOT
            self.clean_preupgrade_environment()
            return 0

        if self.conf.text:
            # Test whether w3m, lynx and elinks packages are installed
            found = False
            for pkg in SystemIdentification.get_convertors():
                if xml_manager.get_package_version(pkg):
                    self.text_convertor = pkg
                    found = True
                    break
            if not found:
                log_message(settings.converter_message.format(
                    ' '.join(SystemIdentification.get_convertors())))
                return ReturnValues.MISSING_TEXT_CONVERTOR

        return_code = self.determine_module_set_location()
        if return_code:
            return return_code
        self.determine_module_set_copy_location()

        if self.conf.list_rules:
            rules = [x for x in
                     XccdfHelper.get_list_rules(self.all_xccdf_xml_path)]
            log_message('\n'.join(rules))
            return 0

        if self.conf.mode and self.conf.select_rules:
            log_message(settings.options_not_allowed)
            return ReturnValues.MODE_SELECT_RULES

        # If force option is not mentioned and user selects NO then exit
        if not self.conf.force:
            text = ""
            if self.conf.dst_arch:
                correct_option = [x for x in settings.migration_options
                                  if self.conf.dst_arch == x]
                if not correct_option:
                    sys.stderr.write(
                        "Error: Specify correct value for --dst-arch"
                        " option.\nValid are: %s.\n"
                        % ", ".join(settings.migration_options)
                    )
                    return ReturnValues.INVALID_CLI_OPTION
            if SystemIdentification.get_arch() == "i386" or \
                    SystemIdentification.get_arch() == "i686":
                if not self.conf.dst_arch:
                    text = '\n' + settings.migration_text
            logger_debug.debug("Architecture '%s'. Text '%s'.",
                               SystemIdentification.get_arch(), text)
            if not show_message(settings.warning_text + text):
                # User does not want to continue
                return ReturnValues.USER_ABORT

        self.openscap_helper = OpenSCAPHelper(self.conf.assessment_results_dir,
                                              self.conf.result_prefix,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.all_xccdf_xml_path)

        if not self.executed_under_root():
            return ReturnValues.ROOT
        if not Application.is_installed_oscap_ok():
            return ReturnValues.MISSING_OPENSCAP

        self.execution_dir = os.getcwd()
        os.chdir("/tmp")
        retval = self.scan_system()
        if retval != 0:
            return retval
        retval = self.summary_report(self.tar_ball_name)
        self.common.copy_common_files()
        KickstartGenerator.kickstart_scripts()
        FileHelper.remove_home_issues()
        if self.conf.upload:
            if not self.upload_results():
                retval = ReturnValues.SEND_REPORT_TO_UI
        os.chdir(self.execution_dir)
        return retval

    def executed_under_root(self):
        if os.geteuid() != 0:
            print("Need to be root", end="\n")
            if not self.conf.debug:
                return False
        return True
