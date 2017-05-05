# -*- coding: utf-8 -*-
"""
The application module serves for running oscap binary and reporting results
to UI.
"""

from __future__ import unicode_literals, print_function
import shutil
import datetime
import os
import sys
import logging
from distutils import dir_util

try:
    from xmlrpclib import Fault
except ImportError:
    from xmlrpc.client import Fault

from preupg import xml_manager, settings
from preupg.common import Common
from preupg.settings import ReturnValues
from preupg.scanning import ScanProgress, ScanningHelper
from preupg.utils import FileHelper, ProcessHelper, DirHelper, OpenSCAPHelper
from preupg.utils import MessageHelper, TarballHelper, SystemIdentification
from preupg.utils import PostupgradeHelper, ConfigHelper, ConfigFilesHelper
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


def list_contents(source_dir):
    """Function returns a list of installed contents"""
    content_dict = {}
    is_dir = lambda x: os.path.isdir(os.path.join(source_dir, x))
    dirs = os.listdir(source_dir)
    for dir_name in filter(is_dir, dirs):
        full_dir_name = os.path.join(source_dir, dir_name,
                                     settings.content_file)
        if os.path.exists(full_dir_name):
            logger_debug.info('%s', dir_name)
            content_dict[dir_name] = full_dir_name
    return content_dict


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
        self.content = ""
        self.result_file = ""
        self.xml_mgr = None
        self.basename = ""
        self.scanning_progress = None
        self.report_parser = None
        self.report_data = {}
        self.text_convertor = ""
        self.common = None
        self._devel_mode = 0
        self._dist_mode = None
        self.report_return_value = 0
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
        self.third_party = ""
        self.assessment_dir = None
        self.list_scans = []

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

    def get_third_party_dir(self, assessment):
        """
        Function returns a 3rdparty dir for upgrade path
        like /root/preupgrade/RHEL6_7/3rdparty
        """
        return os.path.join(assessment, settings.add_ons)

    def get_postupgrade_dir(self):
        """Function returns postupgrade dir"""
        return os.path.join(self.conf.assessment_results_dir,
                            settings.postupgrade_dir)

    def upload_results(self, tarball_path=None):
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
        message = ""
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

    def prepare_scan_directories(self):
        """Used for prepartion of directories used during scan functionality"""
        self.basename = os.path.basename(self.content)
        dirs = [self.conf.assessment_results_dir, settings.tarball_result_dir]
        dirs.extend(os.path.join(self.conf.assessment_results_dir, x) for x in settings.preupgrade_dirs)
        if self.conf.temp_dir:
            dirs.append(self.conf.temp_dir)
        for dir_name in dirs:
            DirHelper.check_or_create_temp_dir(dir_name)

        # Copy README files into proper directories
        for key, val in iter(settings.readme_files.items()):
            shutil.copyfile(os.path.join(settings.source_dir, key),
                            os.path.join(self.conf.assessment_results_dir, val))

    def get_total_check(self):
        """Returns a total check"""
        return self.report_parser.get_number_checks()

    def run_scan_process(self):
        """Function scans the source system"""
        self.xml_mgr = xml_manager.XmlManager(self.conf.assessment_results_dir,
                                              self.get_scenario(),
                                              os.path.basename(self.content),
                                              self.conf.result_prefix)

        self.report_parser.add_global_tags(self.conf.assessment_results_dir,
                                           self.get_proper_scenario(self.get_scenario()),
                                           self.conf.mode,
                                           self._devel_mode,
                                           self._dist_mode)

        self.report_parser.modify_result_path(self.conf.assessment_results_dir,
                                              self.get_proper_scenario(self.get_scenario()),
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
        # fail if openscap wasn't successful; if debug, continue
        return ProcessHelper.run_subprocess(cmd, print_output=False, function=function)

    def get_scenario(self):
        """The function returns scenario"""
        scenario = None
        try:
            sep_content = os.path.dirname(self.content).split('/')
            if self.conf.contents:
                dir_name = SystemIdentification.get_valid_scenario(self.content)
                if dir_name is None:
                    return None
                check_name = dir_name
            else:
                check_name = self.conf.scan
            scenario = [x for x in sep_content if check_name in x][0]
        except IndexError:
            scenario = None
        return scenario

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

    def prepare_for_generation(self):
        """Function prepares the XML file for conversion to HTML format"""
        for report in self._get_reports():
            if self.conf.old_report_style:
                ReportParser.write_xccdf_version(report, direction=True)
            self.openscap_helper.run_generate(report,
                                              report.replace('.xml', '.html'),
                                              old_style=self.conf.old_report_style)
            if self.conf.old_report_style:
                ReportParser.write_xccdf_version(report)

    def prepare_xml_for_html(self):
        """The function prepares a XML file for HTML creation"""
        # Reload XML file
        self.report_parser.reload_xml(self.openscap_helper.get_default_xml_result_path())
        # Replace fail in case of slight and medium risks with needs_inspection
        self.report_parser.replace_inplace_risk(scanning_results=self.scanning_progress)
        if not self.conf.debug:
            self.report_parser.remove_debug_info()
        self.report_parser.reload_xml(self.openscap_helper.get_default_xml_result_path())
        self.report_parser.update_check_description()
        self.prepare_for_generation()

        if not self.conf.verbose:
            self.xml_mgr.remove_html_information()
        # This function finalize XML operations
        self.finalize_xml_files()
        if self.conf.text:
            ProcessHelper.run_subprocess(self.get_cmd_convertor(), print_output=False, shell=True)

    def _get_reports(self):
        reports = [self.openscap_helper.get_default_xml_result_path()]
        return reports

    def finalize_xml_files(self):
        """
        Function copies postupgrade scripts and creates hash postupgrade file.
        It finds solution files and update XML file.
        """
        # Copy postupgrade.d special files
        PostupgradeHelper.special_postupgrade_scripts(self.conf.assessment_results_dir)
        PostupgradeHelper.hash_postupgrade_file(self.conf.verbose, self.get_postupgrade_dir())

        solution_files = self.report_parser.get_solution_files()
        for report in self._get_reports():
            self.xml_mgr.find_solution_files(report.split('.')[0], solution_files)

    def set_third_party(self, third_party):
        self.third_party = third_party

    def run_third_party_modules(self, dir_name):
        """
        Functions executes a 3rd party contents

        3rd party contents are stored in
        /usr/share/preupgrade/RHEL6_7/3rdparty directory
        """
        for third_party, content in iter(list_contents(dir_name.items())):
            third_party_name = self.third_party = third_party
            log_message("Execution {0} assessments:".format(third_party))
            self.report_parser.reload_xml(content)
            self.content = content
            self.run_scan_process()
            self.report_data[third_party_name] = self.scanning_progress.get_output_data()
            # This function prepare XML and generate HTML
            self.prepare_xml_for_html()
        self.set_third_party("")

    def get_cmd_convertor(self):
        """Function returns cmd with text convertor string"""
        cmd = settings.text_converters[self.text_convertor].format(
            self.text_convertor,
            self.openscap_helper.get_default_html_result_path(),
            self.openscap_helper.get_default_txt_result_path()
        )
        return cmd

    def get_proper_scenario(self, scenario):
        if not self.conf.contents:
            return scenario
        scenario = scenario.replace('-results', '')
        return scenario

    def prepare_scan_system(self):
        """Function cleans previous scan and creates relevant directories"""
        # First of all we need to delete the older one assessment
        self.clean_scan()
        self.prepare_scan_directories()
        scenario = self.get_scenario()
        if scenario is None:
            log_message('Invalid scenario: %s' % self.conf.contents)
            return ReturnValues.SCENARIO
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        if not os.path.isdir(scenario_path):
            log_message('Invalid scenario: %s' % scenario,
                        level=logging.ERROR)
            return ReturnValues.SCENARIO
        return 0

    def generate_report(self):
        """Function generates report"""
        scenario = self.get_scenario()
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        self.assessment_dir = os.path.join(self.conf.assessment_results_dir, self.get_proper_scenario(scenario))
        dir_util.copy_tree(scenario_path, self.assessment_dir)
        # Try copy directory with contents to /root/preupgrade
        # Call xccdf_compose API for generating all-xccdf.xml
        if not self.conf.contents:
            xccdf_compose = XCCDFCompose(self.assessment_dir)
            ret_val = xccdf_compose.generate_xml(generate_from_ini=False)
            if ret_val != 0:
                return ret_val
            if os.path.isdir(self.assessment_dir):
                shutil.rmtree(self.assessment_dir)
            shutil.move(xccdf_compose.get_compose_dir_name(), self.assessment_dir)

        self.common.prep_symlinks(self.assessment_dir,
                                  scenario=self.get_proper_scenario(scenario))
        if not self.conf.contents:
            XccdfHelper.update_platform(os.path.join(self.assessment_dir, settings.content_file))
        else:
            XccdfHelper.update_platform(self.content)
            self.assessment_dir = os.path.dirname(self.content)
        return 0

    def copy_preupgrade_scripts(self, assessment_dir):
        # Copy preupgrade-scripts directory from scenarvirtuio
        preupg_scripts = os.path.join(assessment_dir,
                                      settings.preupgrade_scripts_dir)
        if os.path.exists(preupg_scripts):
            dir_util.copy_tree(preupg_scripts,
                               settings.preupgrade_scripts_path)

    def scan_system(self):
        """The function is used for scanning system with all steps."""
        self._set_devel_mode()
        ret_val = self.prepare_scan_system()
        if ret_val != 0:
            return ret_val
        ret_val = self.generate_report()
        if ret_val != 0:
            return ret_val
        # Update source XML file in temporary directory
        self.content = os.path.join(self.assessment_dir, settings.content_file)
        self.openscap_helper.update_variables(self.conf.assessment_results_dir,
                                              self.conf.result_prefix,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.content)
        try:
            self.report_parser = ReportParser(self.content)
        except IOError:
            log_message("The module {0} does not exist.".format(self.content))
            return ReturnValues.SCENARIO
        if not self.conf.contents:
            version = SystemIdentification.get_assessment_version(
                self.conf.scan)
            if version is None:
                log_message("Your scan is in a wrong format %s." % version,
                            level=logging.ERROR)
                log_message("It should be like 'RHEL6_7' for upgrade from"
                            " RHEL 6->7.", level=logging.ERROR)
                return ReturnValues.SCENARIO
            self.report_parser.modify_platform_tag(version[0])
        if self.conf.mode:
            lines = [i.rstrip() for i in
                     FileHelper.get_file_content(
                         os.path.join(self.assessment_dir, self.conf.mode),
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
        # This function prepare XML and generate HTML
        self.prepare_xml_for_html()

        third_party_dir_name = self.get_third_party_dir(self.assessment_dir)
        if os.path.exists(third_party_dir_name):
            self.run_third_party_modules(third_party_dir_name)

        self.copy_preupgrade_scripts(self.assessment_dir)
        ConfigFilesHelper.copy_modified_config_files(
            settings.assessment_results_dir)

        # It prints out result in table format
        ScanningHelper.format_rules_to_table(main_report, "main contents")
        for target, report in iter(self.report_data.items()):
            ScanningHelper.format_rules_to_table(report, "3rdparty content " + target)

        self.tar_ball_name = TarballHelper.tarball_result_dir(self.conf.tarball_name, self.conf.assessment_results_dir, self.conf.verbose)
        log_message("The tarball with results is stored in '%s' ." % self.tar_ball_name)
        log_message("The latest assessment is stored in the '%s' directory." % self.conf.assessment_results_dir)
        # pack all configuration files to tarball
        return 0

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
            "Read the file {0} for more details.".
            format(path),
            3: 'We have found some error issues. In-place upgrade or migration is not advised.\n' +
               "Read the file {0} for more details.".format(path)
        }
        self.report_return_value = XccdfHelper.check_inplace_risk(self.openscap_helper.get_default_xml_result_path(), 0)
        try:
            if report_dict[int(self.report_return_value)]:
                log_message('Summary information:')
                log_message(report_dict[int(self.report_return_value)])
        except KeyError:
            # We do not want to print anything in case of testing contents
            pass
        if not self.conf.mode or self.conf.mode == "upgrade":
            # User either has not specied mode (upgrade and migration both
            # together by default) or has chosen upgrade only = print warning
            # to backup the system before doing the in-place upgrade
            log_message(settings.upgrade_backup_warning)
        if self.report_data:
            log_message('Summary of the third party providers:')
            for target, dummy_report in iter(self.report_data.items()):
                self.third_party = target
                log_message("Read the third party content {0} {1} for more details.".
                            format(target, path))
        log_message("Upload results to UI by the command:\ne.g. {0} .".format(command))

    def _set_devel_mode(self):
        # Check for devel_mode
        if os.path.exists(settings.DEVEL_MODE):
            self._devel_mode = 1
            self._dist_mode = ConfigHelper.get_preupg_config_file(
                settings.PREUPG_CONFIG_FILE, 'dist_mode', section="devel-mode")
        else:
            self._devel_mode = 0

    def _check_available_contents(self):
        cnt = 0
        is_dir = lambda x: os.path.isdir(os.path.join(self.conf.source_dir, x))
        dirs = os.listdir(self.conf.source_dir)
        self.list_scans = []
        for dir_name in filter(is_dir, dirs):
            if SystemIdentification.get_assessment_version(dir_name):
                self.conf.scan = dir_name
                self.list_scans.append(dir_name)
                logger_debug.debug("Scan directory '%s'", self.conf.scan)
                cnt += 1

        if int(cnt) < 1:
            log_message("There were no modules found in the %s directory.\n"
                        "If you would like to use this tool, you have to"
                        " install some." % settings.source_dir)
            return ReturnValues.SCENARIO
        if int(cnt) > 1:
            log_message("Preupgrade Assistant detects more "
                        "than one set of modules in the %s directory.\n" % settings.source_dir)
            log_message("The list of sets of all available modules is: \n%s" % '\n'.join(self.list_scans))
            log_message("If you would like to use the tool, "
                        "specify the correct upgrade path mentioned above with a parameter -s.")
            return ReturnValues.SCENARIO
        return 0

    def run(self):
        """run analysis"""
        version_msg = "Preupgrade Assistant version: %s" % VERSION
        if self.conf.version:
            print (version_msg)
            return 0

        logger_debug.debug(version_msg)
        if self.conf.list_contents_set:
            for dir_name, dummy_content in iter(list_contents(
                    self.conf.source_dir).items()):
                log_message("%s" % dir_name)
            return 0

        if not self.conf.scan and not self.conf.contents and \
                not self.conf.list_rules:
            ret_val = self._check_available_contents()
            if int(ret_val) != 0:
                return ret_val

        if self.conf.list_rules:
            ret_val = self._check_available_contents()
            if int(ret_val) != 0:
                return ret_val
            rules = [self.conf.scan + ':' + x
                     for x in XccdfHelper.get_list_rules(self.conf.scan)]
            log_message('\n'.join(rules))
            return 0

        if self.conf.upload:
            if not self.upload_results():
                return ReturnValues.SEND_REPORT_TO_UI
            return 0

        if self.conf.mode and self.conf.select_rules:
            log_message(settings.options_not_allowed)
            return ReturnValues.MODE_SELECT_RULES

        if not self.conf.riskcheck and not self.conf.cleanup:
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

        if self.conf.text:
            # Test whether w3m, lynx and elinks packages are installed
            found = False
            for pkg in SystemIdentification.get_convertors():
                if xml_manager.get_package_version(pkg):
                    self.text_convertor = pkg
                    found = True
                    break
            if not found:
                log_message(settings.converter_message.format(' '.join(SystemIdentification.get_convertors())))
                return ReturnValues.MISSING_TEXT_CONVERTOR

        if os.geteuid() != 0:
            print("Need to be root", end="\n")
            if not self.conf.debug:
                return ReturnValues.ROOT

        if self.conf.cleanup:
            self.clean_preupgrade_environment()
            return 0

        self.openscap_helper = OpenSCAPHelper(self.conf.assessment_results_dir,
                                              self.conf.result_prefix,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.content)
        if self.conf.riskcheck:
            if not os.path.exists(self.openscap_helper.get_default_xml_result_path()):
                log_message("The 'preupg' command was not run yet. Run it to check for possible risks.")
                return ReturnValues.PREUPG_BEFORE_RISKCHECK
            return_val = XccdfHelper.check_inplace_risk(self.openscap_helper.get_default_xml_result_path(),
                                                        self.conf.verbose)
            return return_val

        if self.conf.scan:
            self.content = os.path.join(self.conf.source_dir,
                                        self.conf.scan,
                                        settings.content_file)
            if self.conf.scan.startswith("/"):
                log_message('Specify the correct upgrade path parameter like -s RHEL6_7')
                log_message("Upgrade path is provided by the 'preupg --list' command.")
                self._check_available_contents()
                log_message("The available upgrade paths: '%s'" % '\n'.join(self.list_scans))
                return ReturnValues.SCENARIO
            if not os.path.isdir(os.path.join(self.conf.source_dir, self.conf.scan)):
                log_message('Specify the correct upgrade path parameter like -s RHEL6_7')
                self._check_available_contents()
                log_message("Upgrade path is provided by the 'preupg --list' command.")
                log_message("The available upgrade paths: '%s'" % '\n'.join(self.list_scans))
                return ReturnValues.SCENARIO

        if self.conf.contents:
            self.content = os.path.join(os.getcwd(), self.conf.contents)
            # From content path like content-users/RHEL6_7 we need
            # to get content-users dir
            content_dir = self.conf.contents[:self.conf.contents.find(self.get_scenario())]
            self.conf.source_dir = os.path.join(os.getcwd(), content_dir)

        self.common = Common(self.conf)
        if not self.conf.skip_common:
            if not self.common.common_results():
                return ReturnValues.SCRIPT_TXT_MISSING

        if self.conf.scan or self.conf.contents:
            if not os.path.exists(settings.openscap_binary):
                log_message("Oscap with SCE enabled is not installed")
                return ReturnValues.MISSING_OPENSCAP
            if not os.access(settings.openscap_binary, os.X_OK):
                log_message("Oscap with SCE %s is not executable"
                            % settings.openscap_binary)
                return ReturnValues.MISSING_OPENSCAP

            current_dir = os.getcwd()
            os.chdir("/tmp")
            retval = self.scan_system()
            if int(retval) != 0:
                return retval
            self.summary_report(self.tar_ball_name)
            self.common.copy_common_files()
            KickstartGenerator.kickstart_scripts()
            FileHelper.remove_home_issues()
            if self.conf.upload:
                self.upload_results(self.tar_ball_name)
            os.chdir(current_dir)
            return self.report_return_value

        log_message('Nothing to do. Give me a task, please.')
        self.conf.settings[2].parser.print_help()
        return 0
