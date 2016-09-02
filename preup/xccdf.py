# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
import os
import six
from operator import itemgetter
from xml.etree import ElementTree

from preup import settings
from preup.settings import ModuleValues
from preup.logger import log_message, logger_report
from preup.utils import FileHelper, SystemIdentification

XMLNS = "{http://checklists.nist.gov/xccdf/1.2}"


class XccdfHelper(object):

    @staticmethod
    def get_and_print_inplace_risk(verbose, inplace_risk):
        """
        The function browse throw the list and find first
        inplace_risk and return corresponding status.
        If verbose mode is used then it prints out
        all inplace risks higher then SLIGHT.
        """
        risks = {
            'SLIGHT:': 2,
            'MEDIUM:': 2,
            'HIGH:': 4,
            'EXTREME:': 6,
        }

        return_value = -1
        for key, val in sorted(six.iteritems(risks), key=itemgetter(1), reverse=False):
            matched = [x for x in inplace_risk if key in x]
            logger_report.debug(matched)
            if matched:
                # if matched and return_value the remember her
                if return_value < val:
                    return_value = val
                # If verbose mode is used and value is bigger then 0 then prints out
                if int(verbose) > 1:
                    log_message('\n'.join(matched))
                elif int(verbose) == 1 and val > 0:
                    log_message('\n'.join(matched))

        return return_value

    @staticmethod
    def get_check_import_inplace_risk(tree):
        """
        Function returns implace risks
        """
        inplace_risk = []
        risk_regex = "preupg\.risk\.(?P<level>\w+): (?P<message>.+)"
        for check in tree.findall(".//" + XMLNS + "check-import"):
            if not check.text:
                continue
            lines = check.text.strip().split('\n')
            for line in lines:
                match = re.match(risk_regex, line)
                if match:
                    logger_report.debug(line)
                    if line not in inplace_risk:
                        inplace_risk.append(line)
        return inplace_risk

    @staticmethod
    def check_inplace_risk(xccdf_file, verbose):
        """
        The function read the content of the file
        and finds out all "preupg.risk" rows in TestResult tree.
        return value is get from function get_and_print_inplace_risk
        """
        message = "'preupg' command was not run yet. Run 'preupg' before getting list of risks."
        try:
            content = FileHelper.get_file_content(xccdf_file, 'rb', False, False)
            if not content:
                # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
                log_message(message)
                return -1
        except IOError:
            # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
            log_message(message)
            return -1

        target_tree = ElementTree.fromstring(content)
        results = {}
        for profile in target_tree.findall(XMLNS + "TestResult"):
            # Collect all inplace risk for each return values
            for rule_result in profile.findall(XMLNS + "rule-result"):
                result_value = None
                for check in rule_result.findall(XMLNS + "result"):
                    result_value = check.text
                if check.text not in results:
                    results[check.text] = []
                inplace_risk = XccdfHelper.get_check_import_inplace_risk(rule_result)
                if not inplace_risk:
                    continue
                for risk in inplace_risk:
                    if risk not in results[result_value]:
                        results[result_value].append(risk)
        logger_report.debug(results)
        return_val = 0
        for result in settings.ORDERED_LIST:
            if result in results:
                current_val = 0
                logger_report.debug('%s found in assessment' % result)
                if not results[result]:
                    ret_val = XccdfHelper.get_and_print_inplace_risk(verbose, results[result])
                    if result == 'fail' and int(ret_val) == -1:
                        current_val = settings.PREUPG_RETURN_VALUES['error']
                    else:
                        current_val = settings.PREUPG_RETURN_VALUES[result]
                else:
                    ret_val = XccdfHelper.get_and_print_inplace_risk(verbose, results[result])
                    logger_report.debug('Return value from "get_and_print_inplace_risk" is %s' % ret_val)
                    if result == 'fail' and int(ret_val) == -1:
                        current_val = settings.PREUPG_RETURN_VALUES['error']
                    elif result in settings.ERROR_RETURN_VALUES and int(ret_val) != -1:
                        current_val = settings.PREUPG_RETURN_VALUES['error']
                    elif int(ret_val) == -1:
                        current_val = settings.PREUPG_RETURN_VALUES[result]
                    else:
                        # EXTREME has to return 2 as FAIL
                        if ret_val == 6:
                            current_val = ModuleValues.FAIL
                        else:
                            # Needs_action has to return 1 as needs_inspection
                            current_val = ModuleValues.NEEDS_INSPECTION
                if return_val < current_val:
                    return_val = current_val
        return return_val

    @staticmethod
    def get_list_rules(scenario):
        main_dir = os.path.join(settings.source_dir, scenario)
        rules = FileHelper.get_file_content(os.path.join(main_dir, settings.file_list_rules), "rb", method=True)
        rules = [x.strip() for x in rules]
        return rules

    @staticmethod
    def update_platform(full_path):
        file_lines = FileHelper.get_file_content(full_path, 'rb', method=True)
        platform = ''
        platform_id = ''
        if not SystemIdentification.get_system():
            platform = settings.CPE_RHEL
        else:
            platform = settings.CPE_FEDORA
        platform_id = SystemIdentification.get_assessment_version(full_path)
        for index, line in enumerate(file_lines):
            if 'PLATFORM_NAME' in line:
                line = line.replace('PLATFORM_NAME', platform)
            if 'PLATFORM_ID' in line:
                line = line.replace('PLATFORM_ID', platform_id[0])
            file_lines[index] = line
        FileHelper.write_to_file(full_path, 'wb', file_lines)
