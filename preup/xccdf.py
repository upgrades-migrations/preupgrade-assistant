# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
import os
import six
from operator import itemgetter
from xml.etree import ElementTree

from preup import utils, settings
from preup.logger import log_message
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
            'NONE:': 0,
            'SLIGHT:': 1,
            'MEDIUM:': 2,
            'HIGH:': 3,
            'EXTREME:': 4,
        }

        return_value = -1
        for key, val in sorted(six.iteritems(risks), key=itemgetter(1), reverse=False):
            matched = [x for x in inplace_risk if key in x]
            if matched:
                # if matched and return_value the remember her
                if return_value < val:
                    return_value = val
                # If verbose mode is used and value is bigger then 0 then prints out
                if int(verbose) > 1:
                    log_message('\n'.join(matched), print_output=verbose)
                elif int(verbose) == 1 and val > 0:
                    log_message('\n'.join(matched), print_output=verbose)

        return return_value

    @staticmethod
    def get_check_import_inplace_risk(tree):
        """
        Function returns implace risks
        """
        inplace_risk = []
        risk_regex = "INPLACERISK: (?P<level>\w+): (?P<message>.+)"
        for check in tree.findall(".//" + XMLNS + "check-import"):
            if not check.text:
                continue
            lines = check.text.strip().split('\n')
            for line in lines:
                match = re.match(risk_regex, line)
                if match:
                    inplace_risk.append(line)
        return inplace_risk

    @staticmethod
    def check_inplace_risk(xccdf_file, verbose):
        """
        The function read the content of the file
        and finds out all INPLACERISK rows in TestResult tree.
        return value is get from function get_and_print_inplace_risk
        """
        try:
            content = FileHelper.get_file_content(xccdf_file, 'rb', False, False)
            if not content:
                # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
                return -1
        except IOError:
            # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
            return -1

        inplace_risk = []
        target_tree = ElementTree.fromstring(content)
        for profile in target_tree.findall(XMLNS + "TestResult"):
            inplace_risk = XccdfHelper.get_check_import_inplace_risk(profile)

        result = XccdfHelper.get_and_print_inplace_risk(verbose, inplace_risk)
        # different behaviour of division between py2 & 3
        if int(result) == -1:
            return -1
        elif int(result) < 2:
            return 0
        elif int(result) < 4:
            return 1
        else:
            return 2

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
