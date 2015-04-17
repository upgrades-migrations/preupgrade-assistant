# -*- coding: utf-8 -*-

import re
import six
from operator import itemgetter
from xml.etree import ElementTree

from preup import utils
from preup.logger import log_message

XMLNS = "{http://checklists.nist.gov/xccdf/1.2}"


def list_groups(xccdf_file):
    """
    list groups of tests from provided xccdf file
    """
    return []


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


def check_inplace_risk(xccdf_file, verbose):
    """
    The function read the content of the file
    and finds out all INPLACERISK rows in TestResult tree.
    return value is get from function get_and_print_inplace_risk
    """
    try:
        content = utils.get_file_content(xccdf_file, 'r', False, False)
        if not content:
            # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
            return -1
    except IOError:
        # WE NEED TO RETURN -1 FOR RED-HAT-UPGRADE-TOOL
        return -1

    inplace_risk = []
    target_tree = ElementTree.fromstring(content)
    for profile in target_tree.findall(XMLNS + "TestResult"):
        inplace_risk = get_check_import_inplace_risk(profile)

    return get_and_print_inplace_risk(verbose, inplace_risk)/2
