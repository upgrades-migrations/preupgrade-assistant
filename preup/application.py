# -*- coding: utf-8 -*-
"""
The application module serves for running oscap binary and reporting results to UI
"""

from __future__ import unicode_literals, print_function
import shutil
import datetime
import os
import six
import logging
from distutils import dir_util

try:
    from xmlrpclib import Fault
except ImportError:
    from xmlrpc.client import Fault

from preup import xml_manager, settings
from preup.common import Common
from preup.scanning import ScanProgress, ScanningHelper
from preup.utils import FileHelper, ProcessHelper, DirHelper
from preup.utils import MessageHelper, TarballHelper, SystemIdentification
from preup.utils import PostupgradeHelper, ConfigHelper, OpenSCAPHelper, ConfigFilesHelper
from preup.xccdf import XccdfHelper
from preup.logger import log_message, LoggerHelper, logger, logger_report, logger_debug
from preup.report_parser import ReportParser
from preup.kickstart.application import KickstartGenerator
from preuputils.compose import XCCDFCompose
from preup.version import VERSION


def fault_repr(self):
    """monkey patching Fault's repr method so newlines are actually interpreted"""
    log_message(self.faultString)
    return "<Fault %s: %s>" % (self.faultCode, self.faultString)

Fault.__repr__ = fault_repr


def list_contents(source_dir):
    """Function returns a list of installed contents"""
    content_dict = {}
    is_dir = lambda x: os.path.isdir(os.path.join(source_dir, x))
    dirs = os.listdir(source_dir)
    for dir_name in filter(is_dir, dirs):
        full_dir_name = os.path.join(source_dir, dir_name, settings.content_file)
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
        """conf is preup.conf.Conf object, contains configuration"""
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

    def _add_report_log_file(self):
        """
        Add the special report log file
        :return:
        """
        try:
            LoggerHelper.add_file_handler(logger_report,
                                          settings.preupg_report_log,
                                          formatter=logging.Formatter("%(asctime)s %(filename)s"
                                                                      ":%(lineno)s %(funcName)s: %(message)s"),
                                          level=logging.DEBUG)
        except (IOError, OSError):
            logger.warning("Can not create report log '%s'", settings.preupg_report_log)
        else:
            self.report_log_file = settings.preupg_report_log

    def _add_debug_log_file(self):
        """
        Add the special report log file
        :return:
        """
        try:
            LoggerHelper.add_file_handler(logger_debug,
                                          settings.preupg_log,
                                          formatter=logging.Formatter("%(asctime)s %(levelname)s\t%(filename)s"
                                                            ":%(lineno)s %(funcName)s: %(message)s"),
                                          level=logging.DEBUG)
        except (IOError, OSError):
            logger.warning("Can not create debug log '%s'", settings.preupg_log)
        else:
            self.debug_log_file = settings.preupg_log

    def get_preupgrade_kickstart(self):
        return settings.PREUPGRADE_KS

    def get_third_party_dir(self, assessment):
        """
        Function returns a 3rdparty dir for upgrade path
        like /root/preupgrade/RHEL6_7/3rdparty
        """
        return os.path.join(assessment, settings.add_ons)

    def get_postupgrade_dir(self):
        """Function returns postupgrade dir"""
        return os.path.join(self.conf.result_dir, settings.postupgrade_dir)

    def upload_results(self, tarball_path=None):
        """upload tarball with results to frontend"""
        import xmlrpclib
        import socket
        url = ""
        if self.conf.upload is True:
            # lets try default configuration
            log_message('You have to specify server where to upload results.')
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
            message = 'Can\'t connect to preupgrade assistant WEB-UI at %s.\n\n' \
                      'Please ensure that package preupgrade-assistant-ui ' \
                      'has been installed on target system and firewall is set up ' \
                      'to allow connections on port 8099.' % url
            log_message(message)
            log_message(ex.__str__())
            return False

        tarball_results = self.conf.results or tarball_path
        file_content = FileHelper.get_file_content(tarball_results, 'rb', False, False)

        binary = xmlrpclib.Binary(file_content)
        host = socket.gethostname()
        response = proxy.submit.submit_new({
            'data': binary,
            'host': host,
        })
        try:
            status = response['status']
        except KeyError:
            log_message('Invalid response from server.')
            log_message("Invalid response from server: %s" % response, level=logging.ERROR)
        else:
            if status == 'OK':
                try:
                    url = response['url']
                except KeyError:
                    log_message('Report submitted successfully.')
                else:
                    log_message('Report submitted successfully. You can inspect it at %s' % url)
            else:
                try:
                    message = response['message']
                    log_message('Report not submitted. Server returned message: ', message)
                    log_message("Report submit: %s (%s)" % (status, message), level=logging.ERROR)
                except KeyError:
                    log_message('Report not submitted. Server returned status: ', status)
                    log_message("Report submit: %s" % status, level=logging.ERROR)

    def prepare_scan_directories(self):
        """Used for prepartion of directories used during scan functionality"""
        self.basename = os.path.basename(self.content)
        dirs = [self.conf.result_dir, settings.tarball_result_dir]
        dirs.extend(os.path.join(self.conf.result_dir, x) for x in settings.preupgrade_dirs)
        if self.conf.temp_dir:
            dirs.append(self.conf.temp_dir)
        for dir_name in dirs:
            DirHelper.check_or_create_temp_dir(dir_name)

        # Copy README files into proper directories
        for key, val in six.iteritems(settings.readme_files):
            shutil.copyfile(os.path.join(settings.share_dir, "preupgrade", key),
                            os.path.join(self.conf.result_dir, val))

    def get_total_check(self):
        """Returns a total check"""
        return self.report_parser.get_number_checks()

    def run_scan_process(self):
        """Function scans the source system"""
        self.xml_mgr = xml_manager.XmlManager(self.conf.result_dir,
                                              self.get_scenario(),
                                              os.path.basename(self.content),
                                              self.conf.result_name)

        self.report_parser.add_global_tags(self.conf.result_dir,
                                           self.get_proper_scenario(self.get_scenario()),
                                           self.conf.mode,
                                           self._devel_mode,
                                           self._dist_mode)

        self.report_parser.modify_result_path(self.conf.result_dir,
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
            "Assessment finished (time %.2d:%.2ds)" % (diff.seconds / 60,
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
        force_directories = [self.conf.result_dir]
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
        if os.path.islink(self.conf.result_dir):
            os.unlink(self.conf.result_dir)
        if os.path.isdir(self.conf.result_dir):
            shutil.rmtree(self.conf.result_dir)

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
        report_admin = self.report_parser.get_report_type(settings.REPORTS[0])
        if report_admin:
            reports.append(report_admin)
        # We separate user contents
        report_user = self.report_parser.get_report_type(settings.REPORTS[1])
        if report_user:
            reports.append(report_user)
        return reports

    def finalize_xml_files(self):
        """
        Function copies postupgrade scripts and creates hash postupgrade file.
        It finds solution files and update XML file.
        """
        # Copy postupgrade.d special files
        PostupgradeHelper.special_postupgrade_scripts(self.conf.result_dir)
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
        for third_party, content in six.iteritems(list_contents(dir_name)):
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
            return 10
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        if not os.path.isdir(scenario_path):
            log_message('Invalid scenario: %s' % scenario,
                        level=logging.ERROR)
            return 10
        return 0

    def generate_report(self):
        """Function generates report"""
        scenario = self.get_scenario()
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        self.assessment_dir = os.path.join(self.conf.result_dir, self.get_proper_scenario(scenario))
        dir_util.copy_tree(scenario_path, self.assessment_dir)
        # Try copy directory with contents to /root/preupgrade
        # Call xccdf_compose API for generating all-xccdf.xml
        if not self.conf.contents:
            xccdf_compose = XCCDFCompose(self.assessment_dir)
            if xccdf_compose.generate_xml(generate_from_ini=False) != 0:
                return 10
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
        preupg_scripts = os.path.join(assessment_dir, settings.preupgrade_name)
        if os.path.exists(preupg_scripts):
            dir_util.copy_tree(preupg_scripts, settings.preupgrade_scripts)

    def scan_system(self):
        """The function is used for scanning system with all steps."""
        self._set_devel_mode()
        if int(self.prepare_scan_system()) != 0:
            return 10
        if int(self.generate_report()) != 0:
            return 10
        # Update source XML file in temporary directory
        self.content = os.path.join(self.assessment_dir, settings.content_file)
        self.openscap_helper.update_variables(self.conf.result_dir,
                                              self.conf.result_name,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.content)
        try:
            self.report_parser = ReportParser(self.content)
        except IOError:
            log_message("Content {0} does not exist".format(self.content))
            return 10
        if not self.conf.contents:
            version = SystemIdentification.get_assessment_version(self.conf.scan)
            if version is None:
                log_message("Your scan have wrong format",
                            level=logging.ERROR)
                log_message("Examples format is like RHEL6_7",
                            level=logging.ERROR)
                return 10
            self.report_parser.modify_platform_tag(version[0])
        if self.conf.mode:
            try:
                lines = [i.rstrip() for i in FileHelper.get_file_content(os.path.join(self.assessment_dir,
                                                                                      self.conf.mode),
                                                                         'rb',
                                                                         method=True)]
            except IOError:
                return
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
        ConfigFilesHelper.copy_modified_config_files(settings.result_dir)

        # It prints out result in table format
        ScanningHelper.format_rules_to_table(main_report, "main contents")
        for target, report in six.iteritems(self.report_data):
            ScanningHelper.format_rules_to_table(report, "3rdparty content " + target)

        self.tar_ball_name = TarballHelper.tarball_result_dir(self.conf.tarball_name, self.conf.result_dir, self.conf.verbose)
        log_message("Tarball with results is stored here '%s' ." % self.tar_ball_name)
        log_message("The latest assessment is stored in directory '%s' ." % self.conf.result_dir)
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
            0: settings.message.format(path),
            1: settings.message.format(path),
            2: 'We found some critical issues. In-place upgrade is not advised.\n' +
            "Read the file {0} for more details.".
            format(path),
            3: 'We found some error issues. In-place upgrade is not advised.\n' +
               "Read the file {0} for more details.".format(path)

        }
        self.report_return_value = XccdfHelper.check_inplace_risk(self.openscap_helper.get_default_xml_result_path(), 0)
        try:
            if report_dict[int(self.report_return_value)]:
                log_message('Summary information:')
                log_message(report_dict[int(self.report_return_value)])
            for report_type in settings.REPORTS:
                file_name = settings.result_name + '-' + report_type + '.html'
                report_name = os.path.join(os.path.dirname(self.report_parser.get_path()), file_name)
                if os.path.exists(report_name):
                    log_message("Read the %s report file %s for more details." % (report_type, report_name))
        except KeyError:
            # We do not want to print anything in case of testing contents
            pass
        if self.report_data:
            log_message('Summary 3rd party providers:')
            for target, dummy_report in six.iteritems(self.report_data):
                self.third_party = target
                log_message("Read the 3rd party content {0} {1} for more details.".
                            format(target, path))
        log_message("Upload results to UI by command:\ne.g. {0} .".format(command))

    def _set_devel_mode(self):
        # Check for devel_mode
        if os.path.exists(settings.DEVEL_MODE):
            self._devel_mode = 1
            self._dist_mode = ConfigHelper.get_preupg_config_file(settings.PREUPG_CONFIG_FILE,
                                                           'dist_mode',
                                                           section="devel-mode")
        else:
            self._devel_mode = 0

    def run(self):
        """run analysis"""
        version_msg = "Preupgrade Assistant version: %s" % VERSION
        if self.conf.version:
            print (version_msg)
            return 0

        logger_debug.debug(version_msg)
        if self.conf.list_contents_set:
            for dir_name, dummy_content in six.iteritems(list_contents(self.conf.source_dir)):
                log_message("%s" % dir_name)
            return 0

        if not self.conf.scan and not self.conf.contents and not self.conf.list_rules:
            cnt = 0
            is_dir = lambda x: os.path.isdir(os.path.join(self.conf.source_dir, x))
            dirs = os.listdir(self.conf.source_dir)
            for dir_name in filter(is_dir, dirs):
                if SystemIdentification.get_assessment_version(dir_name):
                    self.conf.scan = dir_name
                    logger_debug.debug("Scan directory '%s'", self.conf.scan)
                    cnt += 1

            if int(cnt) < 1:
                log_message("There were no contents found in directory %s. \
If you would like to use this tool, you have to install some." % settings.source_dir)
                return 10
            if int(cnt) > 1:
                log_message("Preupgrade assistant detects more then 1 set of contents in directory %s.\n\
If you would like to use this tool, you have to specify correct upgrade path parameter like -s RHEL6_7." % settings.source_dir)
                return 10

        if self.conf.list_rules:
            list_scans = []
            cnt = 0
            if not self.conf.scan:
                is_dir = lambda x: os.path.isdir(os.path.join(self.conf.source_dir, x))
                dirs = os.listdir(self.conf.source_dir)
                for dir_name in filter(is_dir, dirs):
                    if SystemIdentification.get_assessment_version(dir_name):
                        list_scans.append(dir_name)
                        self.conf.scan = dir_name
                        cnt += 1

                if int(cnt) < 1:
                    log_message("There were no contents found in directory %s. \
                If you would like to use this tool, you have to install some." % settings.source_dir)
                    return 10
                if int(cnt) > 1:
                    log_message("Preupgrade assistant detects more then 1 set of contents in directory %s.\n\
            If you would like to use this tool, you have to specify correct upgrade path parameter like -s RHEL6_7." % settings.source_dir)
                    return 10
            rules = [self.conf.scan + ':' + x for x in XccdfHelper.get_list_rules(self.conf.scan)]
            log_message('\n'.join(rules))
            return 0

        if self.conf.upload and self.conf.results:
            if not self.upload_results():
                return 18
            return 0

        if self.conf.mode and self.conf.select_rules:
            log_message(settings.options_not_allowed)
            return 11

        if not self.conf.riskcheck and not self.conf.cleanup and not self.conf.kickstart:
            # If force option is not mentioned and user select NO then exits
            if not self.conf.force:
                text = ""
                if self.conf.dst_arch:
                    correct_option = [x for x in settings.migration_options if self.conf.dst_arch == x]
                    if not correct_option:
                        log_message("Specify correct --dst-arch option.")
                        log_message("Available are '%s' or '%s'" % (settings.migration_options[0],
                                                                    settings.migration_options[1]))
                        return 12
                if SystemIdentification.get_arch() == "i386" or SystemIdentification.get_arch() == "i686":
                    text = '\n' + settings.migration_text
                logger_debug.debug("Architecture '%s'. Text '%s'.", SystemIdentification.get_arch(), text)
                if not show_message(settings.warning_text + text):
                    # We do not want to continue
                    return 12

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
                return 16

        if os.geteuid() != 0:
            print("Need to be root", end="\n")
            if not self.conf.debug:
                return 13

        if self.conf.cleanup:
            self.clean_preupgrade_environment()
            return 0

        self.openscap_helper = OpenSCAPHelper(self.conf.result_dir,
                                              self.conf.result_name,
                                              self.conf.xml_result_name,
                                              self.conf.html_result_name,
                                              self.content)
        if self.conf.riskcheck:
            if not os.path.exists(self.openscap_helper.get_default_xml_result_path()):
                log_message("'preupg' command was not run yet. Run them before checking risks.")
                return 14
            return_val = XccdfHelper.check_inplace_risk(self.openscap_helper.get_default_xml_result_path(),
                                                        self.conf.verbose)
            return return_val

        if self.conf.kickstart:
            if not os.path.exists(self.openscap_helper.get_default_xml_result_path()):
                log_message("'preupg' command was not run yet. Run them before kickstart generation.")
                return 14
            kg = KickstartGenerator(self.conf, settings.KS_DIR, self.get_preupgrade_kickstart())
            kg.main()
            return 0

        if self.conf.scan:
            self.content = os.path.join(self.conf.source_dir,
                                        self.conf.scan,
                                        settings.content_file)
            if self.conf.scan.startswith("/"):
                log_message('Specify correct upgrade path parameter like -s RHEL6_7')
                log_message('Upgrade path is provided by command preupg --list')
                return 10
            if not os.path.isdir(os.path.join(self.conf.source_dir, self.conf.scan)):
                log_message('Specify correct upgrade path parameter like -s RHEL6_7')
                log_message('Upgrade path is provided by command preupg --list')
                return 10

        if self.conf.contents:
            self.content = os.path.join(os.getcwd(), self.conf.contents)
            # From content path like content-users/RHEL6_7 we need
            # to get content-users dir
            content_dir = self.conf.contents[:self.conf.contents.find(self.get_scenario())]
            self.conf.source_dir = os.path.join(os.getcwd(), content_dir)

        self.common = Common(self.conf)
        if not self.conf.skip_common:
            if not self.common.common_results():
                return 17

        if self.conf.scan or self.conf.contents:
            if not os.path.exists(settings.openscap_binary):
                log_message("Oscap with SCE enabled is not installed")
                return 15
            if not os.access(settings.openscap_binary, os.X_OK):
                log_message("Oscap with SCE %s is not executable" % settings.openscap_binary)
                return 15

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
