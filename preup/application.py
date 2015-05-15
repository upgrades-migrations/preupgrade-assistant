# -*- coding: utf-8 -*-
"""
The application module serves for running oscap binary and reporting results to UI
"""

from __future__ import unicode_literals, print_function
import shutil
import datetime
import os
import sys
import six
from distutils import dir_util

try:
    from xmlrpclib import Fault
except ImportError:
    from xmlrpc.client import Fault

from preup import xccdf, xml_manager, remediate, utils, settings
from preup.common import Common
from preup.scanning import ScanProgress, format_rules_to_table
from preup.utils import check_xml, get_file_content, check_or_create_temp_dir
from preup.utils import run_subprocess, get_assessment_version, get_message
from preup.utils import tarball_result_dir, get_system
from preup.logger import log_message, logging
from preup.report_parser import ReportParser
from preup.kickstart import KickstartGenerator
from preuputils.compose import XCCDFCompose


def get_xsl_stylesheet():
    """Return full XSL stylesheet path"""
    return os.path.join(settings.share_dir, "preupgrade", "xsl", settings.xsl_sheet)


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
            log_message('%s' % dir_name, print_output=False)
            content_dict[dir_name] = full_dir_name

    return content_dict


def show_message(message):
    """
    Prints message out on stdout message (kind of yes/no) and return answer.

    Return values are:
    Return True on accept (y/yes). Otherwise returns False
    """
    accept = ['y', 'yes']
    choice = get_message(title=message)
    if choice in accept:
        return True
    else:
        return False


class Application(object):

    """Class for oscap binary and reporting results to UI"""

    binary = "/usr/bin/oscap"
    command_eval = ['xccdf', 'eval']
    command_remediate = ['xccdf', 'remediate']

    def __init__(self, conf):
        """conf is preup.conf.Conf object, contains configuration"""
        self.conf = conf
        self.content = ""
        self.result_file = ""
        self.xml_mgr = None
        self.basename = ""
        self.scanning_progress = None
        self.report_parser = None
        self.third_party = ""
        self.report_data = {}
        self.text_convertor = ""
        self.common = None

    def get_command_generate(self):
        if not get_system():
            command_generate = ['xccdf', 'generate', 'custom']
        else:
            command_generate = ['xccdf', 'generate', 'report']
        return command_generate

    def get_third_party_name(self):
        """Function returns correct third party name"""
        if self.third_party != "" and not self.third_party.endswith("_"):
            self.third_party += "_"
        return self.third_party

    def get_default_xml_result_path(self):
        """Returns full XML result path"""
        return os.path.join(self.conf.result_dir,
                            self.get_third_party_name() + self.conf.xml_result_name)

    def get_default_html_result_path(self):
        """Returns full HTML result path"""
        return os.path.join(self.conf.result_dir,
                            self.get_third_party_name() + self.conf.html_result_name)

    def get_default_tarball_path(self):
        """Returns full tarball path"""
        return os.path.join(self.conf.result_dir, self.conf.tarball_name)

    def get_default_txt_result_path(self):
        """
        Function returns default txt result path based on result_dir

        :return: default txt result path
        """
        return os.path.join(self.conf.result_dir,
                            self.get_third_party_name() + self.conf.result_name + ".txt")

    def get_binary(self):
        """
        Returns oscap binary

        :return: list with path to oscap binary
        """
        return [self.binary]

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

    def build_generate_command(self, xml_file, html_file):
        """Function builds a command for generating results"""
        command = self.get_binary()
        command.extend(self.get_command_generate())
        if not get_system():
            command.extend(("--stylesheet", get_xsl_stylesheet()))
        command.extend(("--output", html_file))
        command.append(check_xml(xml_file))
        return command

    def build_command(self):
        """create command from configuration"""
        self.result_file = self.get_default_xml_result_path()
        command = self.get_binary()
        report = self.get_default_html_result_path()
        command.extend(self.command_eval)
        command.append('--progress')
        command.extend(('--profile', self.conf.profile))

        # take name of content and create report: <content_name>.html
        #command.extend(('--report', report))
        command.extend(("--results", self.result_file))
        command.append(check_xml(self.content))
        return command

    def upload_results(self, tarball_path=None):
        """upload tarball with results to frontend"""
        import xmlrpclib
        import socket
        if self.conf.upload is True:
            # lets try default configuration
            url = "http://127.0.0.1:8099/submit/"
        else:
            url = self.conf.upload \
                if self.conf.upload[-1] == '/' \
                else self.conf.upload + '/'
        try:
            proxy = xmlrpclib.ServerProxy(url)
            proxy.submit.ping()
        except Exception:
            raise Exception('Can\'t connect to preupgrade assistant WEB-UI at %s.\n\n'
                'Please ensure that package preupgrade-assistant-ui '
                'has been installed on target system and firewall is set up '
                'to allow connections on port 8099.' % url)

        tarball_results = self.conf.results or tarball_path
        file_content = get_file_content(tarball_results, 'rb')

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

    def apply_scan(self):
        """Extract tar ball for remediation"""
        self.prepare_apply_directories()
        tarball_result_dir(self.conf.apply,
                           self.conf.result_dir,
                           self.conf.verbose,
                           direction=False)
        if remediate.hash_postupgrade_file(self.conf.verbose, self.get_postupgrade_dir(), check=True):
            remediate.postupgrade_scripts(self.conf.verbose, self.get_postupgrade_dir())

    def prepare_scan_directories(self):
        """Used for prepartion of directories used during scan functionality"""
        self.basename = os.path.basename(self.content)
        #today = datetime.datetime.today()
        if not self.conf.temp_dir:
            check_or_create_temp_dir(self.conf.result_dir)
        check_or_create_temp_dir(self.conf.result_dir)
        check_or_create_temp_dir(settings.tarball_result_dir)
        for dir_name in settings.preupgrade_dirs:
            check_or_create_temp_dir(os.path.join(self.conf.result_dir, dir_name))

        # Copy README files into proper directories
        for key, val in six.iteritems(settings.readme_files):
            shutil.copyfile(os.path.join(settings.share_dir, "preupgrade", key),
                            os.path.join(self.conf.result_dir, val))

    def prepare_apply_directories(self):
        """Used for preparation of directories during remedation"""

        check_or_create_temp_dir(self.conf.result_dir)

    def get_total_check(self):
        """Returns a total check"""
        return self.report_parser.get_number_checks()

    def run_scan_process(self):
        """Function scans the source system"""
        self.xml_mgr = xml_manager.XmlManager(self.conf.result_dir,
                                              self.get_scenario(),
                                              os.path.basename(self.content),
                                              self.conf.result_name)

        self.report_parser.modify_result_path(self.conf.result_dir,
                                              self.get_proper_scenario(self.get_scenario()),
                                              self.conf.mode)
        # Execute assessment
        self.scanning_progress = ScanProgress(self.get_total_check(), self.conf.debug)
        self.scanning_progress.set_names(self.report_parser.get_name_of_checks())
        log_message('%s:' % settings.assessment_text,
                    new_line=True,
                    log=False)
        log_message('%.3d/%.3d ...running (%s)' % (
                    1,
                    self.get_total_check(),
                    self.scanning_progress.get_full_name(0)),
                    new_line=False,
                    log=False)
        start_time = datetime.datetime.now()
        self.run_scan(function=self.scanning_progress.show_progress)
        end_time = datetime.datetime.now()
        diff = end_time - start_time
        log_message(
            "Assessment finished (time %.2d:%.2ds)" % (diff.seconds/60,
                                                       diff.seconds%60),
            log=False
        )

    def run_scan(self, function=None):
        """
        The function is used for either scanning system or
        for applying changes on the target system
        """
        cmd = self.build_command()
        #log(self.conf.verbose, "running command:\n%s", ' '.join(cmd))
        # fail if openscap wasn't successful; if debug, continue
        return run_subprocess(cmd, print_output=False, function=function)

    def run_generate(self, xml_file, html_file):
        """
        The function generates result.html file from result.xml file
        which was modified by preupgrade assistant
        """
        cmd = self.build_generate_command(xml_file, html_file)
        return run_subprocess(cmd, print_output=True)

    def get_scenario(self):
        """The function returns scenario"""
        scenario = None
        try:
            sep_content = os.path.dirname(self.content).split('/')
            if self.conf.contents:
                dir_name = utils.get_valid_scenario(self.content)
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
        clean_directories = [os.path.join(settings.cache_dir, settings.common_name),
                             settings.log_dir]
        delete_directories = [self.conf.result_dir,
                              settings.tarball_result_dir]
        for dir_name in clean_directories:
            utils.clean_directory(dir_name, '*.log')
        for dir_name in delete_directories:
            if os.path.isdir(dir_name):
                shutil.rmtree(dir_name)

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
        # We separate admin contents
        reports = [self.get_default_xml_result_path()]
        report_admin = self.report_parser.get_report_type(settings.REPORTS[0])
        if report_admin:
            reports.append(report_admin)
        # We separate user contents
        report_user = self.report_parser.get_report_type(settings.REPORTS[1])
        if report_user:
            reports.append(report_user)
        for report in reports:
            ReportParser.write_xccdf_version(report, direction=True)
            self.run_generate(report, report.replace('.xml', '.html'))
            # Switching back namespace
            ReportParser.write_xccdf_version(report)

    def prepare_xml_for_html(self):
        """The function prepares a XML file for HTML creation"""
        # Reload XML file
        self.report_parser.reload_xml(self.get_default_xml_result_path())
        # Replace fail in case of none or slight risk with needs_inspection
        self.report_parser.replace_inplace_risk(scanning_results=self.scanning_progress)
        if not self.conf.debug:
            self.report_parser.remove_debug_info()
        self.report_parser.reload_xml(self.get_default_xml_result_path())
        self.report_parser.update_check_description()
        self.prepare_for_generation()

        if not self.conf.verbose:
            self.xml_mgr.remove_html_information()
        # This function finalize XML operations
        self.finalize_xml_files()
        if self.conf.text:
            run_subprocess(self.get_cmd_convertor(),
                           print_output=False,
                           shell=True)

    def finalize_xml_files(self):
        """
        Function copies postupgrade scripts and creates hash postupgrade file.
        It finds solution files and update XML file.
        """
        # Copy postupgrade.d special files
        remediate.special_postupgrade_scripts(self.conf.result_dir)
        remediate.hash_postupgrade_file(self.conf.verbose,
                                        self.get_postupgrade_dir())
        self.xml_mgr.find_solution_files(self.report_parser.get_solution_files())
        remediate.copy_modified_config_files(self.conf.result_dir)

    def run_third_party_modules(self, dir_name):
        """
        Functions executes a 3rd party contents

        3rd party contents are stored in
        /usr/share/preupgrade/RHEL6_7/3rdparty directory
        """
        for self.third_party, content in six.iteritems(list_contents(dir_name)):
            third_party_name = self.third_party
            log_message("Execution {0} assessments:".format(self.third_party))
            self.report_parser.reload_xml(content)
            self.content = content
            self.run_scan_process()
            self.report_data[third_party_name] = self.scanning_progress.get_output_data()
            # This function prepare XML and generate HTML
            self.prepare_xml_for_html()

        self.third_party = ""

    def get_cmd_convertor(self):
        """Function returns cmd with text convertor string"""
        cmd = settings.text_converters[self.text_convertor].format(
            self.text_convertor,
            self.get_default_html_result_path(),
            self.get_default_txt_result_path()
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
            sys.exit(3)
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        if not os.path.isdir(scenario_path):
            log_message('Invalid scenario: %s' % scenario,
                        level=logging.ERROR)
            sys.exit(3)

    def generate_report(self):
        """Function generates report"""
        scenario = self.get_scenario()
        scenario_path = os.path.join(self.conf.source_dir, scenario)
        assessment_dir = os.path.join(self.conf.result_dir,
                                      self.get_proper_scenario(scenario))
        dir_util.copy_tree(scenario_path, assessment_dir)
        # Try copy directory with contents to /root/preupgrade
        # Call xccdf_compose API for generating all-xccdf.xml
        if not self.conf.contents:
            xccdf_compose = XCCDFCompose(assessment_dir)
            generated_dir = xccdf_compose.generate_xml(generate_from_ini=False)
            if os.path.isdir(assessment_dir):
                shutil.rmtree(assessment_dir)
            shutil.move(generated_dir, assessment_dir)

        self.common.prep_symlinks(assessment_dir,
                                  scenario=self.get_proper_scenario(scenario))
        if not self.conf.contents:
            utils.update_platform(os.path.join(assessment_dir, settings.content_file))
        else:
            utils.update_platform(self.content)
            assessment_dir = os.path.dirname(self.content)
        return assessment_dir

    def copy_preupgrade_scripts(self, assessment_dir):
        # Copy preupgrade-scripts directory from scenarvirtuio
        preupg_scripts = os.path.join(assessment_dir, settings.preupgrade_name)
        if os.path.exists(preupg_scripts):
            dir_util.copy_tree(preupg_scripts, settings.preupgrade_scripts)

    def scan_system(self):
        """The function is used for scanning system with all steps."""
        self.prepare_scan_system()
        assessment_dir = self.generate_report()
        # Update source XML file in temporary directory
        self.content = os.path.join(assessment_dir, settings.content_file)
        try:
            self.report_parser = ReportParser(self.content)
        except IOError:
            log_message("Content {0} does not exist".format(self.content))
            sys.exit(1)
        if not self.conf.contents:
            version = get_assessment_version(self.conf.scan)
            if version is None:
                log_message("Your scan have wrong format",
                            level=logging.ERROR)
                log_message("Examples format is like RHEL6_7",
                            level=logging.ERROR)
                sys.exit(1)
            self.report_parser.modify_platform_tag(version[0])
        if self.conf.mode:
            self.report_parser.select_rules(self.conf.mode)
        self.run_scan_process()
        main_report = self.scanning_progress.get_output_data()
        # This function prepare XML and generate HTML
        self.prepare_xml_for_html()

        third_party_dir_name = self.get_third_party_dir(assessment_dir)
        if os.path.exists(third_party_dir_name):
            self.run_third_party_modules(third_party_dir_name)

        self.copy_preupgrade_scripts(assessment_dir)

        # It prints out result in table format
        format_rules_to_table(main_report, "main contents")
        for target, report in six.iteritems(self.report_data):
            format_rules_to_table(report, "3rdparty content " + target)

        tar_ball_name = tarball_result_dir(self.conf.tarball_name, self.conf.result_dir, self.conf.verbose)
        log_message("Tarball with results is stored here %s ." % tar_ball_name)
        log_message("The latest assessment is stored in directory %s ." % self.conf.result_dir)
        # pack all configuration files to tarball
        return tar_ball_name

    def summary_report(self):
        """Function prints a summary report"""
        command = settings.ui_command.format(settings.tarball_result_dir)
        if self.conf.text:
            path = self.get_default_txt_result_path()
        else:
            path = self.get_default_html_result_path()

        report_dict = {
            0: settings.message.format(path),
            1: settings.message.format(path),
            2: 'We found some critical issues. In-place upgrade is not advised.\n' +
            "Read the file {0} for more details.".
            format(path)
        }
        return_value = xccdf.check_inplace_risk(self.get_default_xml_result_path(), 0)
        try:
            if report_dict[int(return_value)]:
                log_message('Summary information:')
                log_message(report_dict[int(return_value)])
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

    def run(self):
        """run analysis"""
        if self.conf.list_contents_set:
            for dir_name, dummy_content in six.iteritems(list_contents(self.conf.source_dir)):
                log_message("{0}".format(dir_name))
            return 0

        if self.conf.upload and self.conf.results:
            self.upload_results()
            return 0

        if not self.conf.riskcheck and not self.conf.apply and not self.conf.cleanup and not self.conf.kickstart:
            # If force option is not mentioned and user select NO then exits
            if not self.conf.force and not show_message(settings.warning_text):
                # We do not want to continue
                return 0

        if self.conf.text:
            # Test whether w3m, lynx and elinks packages are installed
            found = False
            for pkg in utils.get_convertors():
                if xml_manager.get_package_version(pkg):
                    self.text_convertor = pkg
                    found = True
                    break
            if not found:
                log_message(settings.converter_message.format(' '.join(utils.get_convertors())))
                return 0

        if os.geteuid() != 0:
            print("Need to be root", end="\n")
            if not self.conf.debug:
                return 2

        if self.conf.cleanup:
            self.clean_preupgrade_environment()
            sys.exit(0)

        if self.conf.riskcheck:
            return_val = xccdf.check_inplace_risk(self.get_default_xml_result_path(), self.conf.verbose)
            return return_val

        if self.conf.kickstart:
            kg = KickstartGenerator(self.get_preupgrade_kickstart())
            KickstartGenerator.copy_kickstart_templates()
            dummy_ks = kg.generate()
            log_message('Kickstart for migration is {0}'.format(self.get_preupgrade_kickstart()))
            return 0

        if not self.conf.scan and not self.conf.contents:
            cnt = 0
            is_dir = lambda x: os.path.isdir(os.path.join(self.conf.source_dir, x))
            dirs = os.listdir(self.conf.source_dir)
            for dir_name in filter(is_dir, dirs):
                if utils.get_assessment_version(dir_name):
                    self.conf.scan = dir_name
                    cnt += 1

            if int(cnt) < 1:
                log_message("There were no contents found in directory %s. \
If you would like to use this tool, you have to install some." % settings.source_dir)
                return 1
            if int(cnt) > 1:
                log_message("There only 1 set of contents is allowed directory %s. \
If you would like to use this tool, you have to have only one." % settings.source_dir)
                return 1

        if self.conf.scan:
            self.content = os.path.join(self.conf.source_dir,
                                        self.conf.scan,
                                        settings.content_file)
            if self.conf.scan.startswith("/"):
                log_message('Specify correct upgrade path parameter like -s RHEL6_7')
                log_message('Upgrade path is provided by command preupg --list')
                return 1
            if not os.path.isdir(os.path.join(self.conf.source_dir, self.conf.scan)):
                log_message('Specify correct upgrade path parameter like -s RHEL6_7')
                log_message('Upgrade path is provided by command preupg --list')
                return 1

        if self.conf.contents:
            self.content = os.path.join(os.getcwd(), self.conf.contents)
            # From content path like content-users/RHEL6_7 we need
            # to get content-users dir
            content_dir = self.conf.contents[:self.conf.contents.find(self.get_scenario())]
            self.conf.source_dir = os.path.join(os.getcwd(), content_dir)

        self.common = Common(self.conf)
        if not self.conf.skip_common:
            if not self.common.common_results():
                return 1

        if self.conf.scan or self.conf.contents:
            if not os.path.exists(self.binary):
                log_message("Oscap with SCE enabled is not installed")
                return 1
            if not os.access(self.binary, os.X_OK):
                log_message("Oscap with SCE %s is not executable" % self.binary)
                return 1

            current_dir = os.getcwd()
            os.chdir("/tmp")
            tarball_path = self.scan_system()
            self.summary_report()
            self.common.copy_common_files()
            utils.remove_home_issues()
            if self.conf.upload:
                self.upload_results(tarball_path)
            os.chdir(current_dir)
            return 0

        log_message('Nothing to do. Give me a task, please.')
        self.conf.settings[2].parser.print_help()
        return 0
