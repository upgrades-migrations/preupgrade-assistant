#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import sys

from lxml import etree as ET
from preupg.utils import OpenSCAPHelper, ProcessHelper, FileHelper

version = 1.1  # version of the preupg-diff
diff_report_name = "result_diff"
diff_report_name_xml = diff_report_name + ".xml"
diff_report_name_html = diff_report_name + ".html"
namespace = "http://checklists.nist.gov/xccdf/1.2"
# Rule result attributes to be compared for equality
rule_attrs_to_compare = ["result", "solution", "stdout", "stderr"]
parsed_opts = None


def parse_cli_opts():
    parser = argparse.ArgumentParser(
        description="preupg-diff compares multiple Preupgrade Assistant"
        " reports and shows issues that are unique to the last one."
        " For example, you have 3 reports, all of which you have already"
        " analyzed and are aware of issues raised there, and one new"
        " report.  Instead of reading through all items in the new report,"
        " this tool will go through all rule results in the last report"
        " and will hide those that have same content (e.g. solution"
        " proposal and risks) as at least one of the previous reports."
        " The trimmed report is output in XML and HTML format and named"
        " {0}.xml/html.".format(diff_report_name))
    parser.add_argument("analyzed_xml", help="One or more 'old' reports. Risks"
                        " found in these files will be filtered out from the"
                        " output.",
                        nargs='+', metavar="ANALYZED")
    parser.add_argument("new_xml", help="New XML report with possibly"
                        " new issues", metavar="NEW")
    parser.add_argument("-s", "--simple-html", help="Generate simpler HTML"
                        " than the default, without clickable buttons, just"
                        " long scrollable document.", action="store_true")
    parser.add_argument("-v", "--verbose", help="Print more detailed"
                        " information about the processing.",
                        action="store_true")
    parser.add_argument("--version", action="version", version="%(prog)s {0}"
                        .format(version))
    return parser.parse_args()


class ResultXML(object):
    def __init__(self, xml_path):
        self.tree = get_xml_tree_object(xml_path)
        self.root = self.tree.getroot()
        self.get_rules()

    def get_rules(self):
        """This method finds all the rules that has been used during the
        system preassessment and saves the following rule attributes:
        - solution .. solution/remediation text
        - result .. result string, e.g. informational, notapplicable, ..
        - stdout .. string with standard output captured during rule execution
        - stderr .. string with standard error output -||-
        - rule_tag and result_tag .. reference to the XML tag object
        """
        self.rules = {}
        self.get_rule_ids_and_solutions()
        self.get_results_and_outputs()

    def get_rule_ids_and_solutions(self):
        for rule_tag in find_subtags_recursive(self.root, "Rule"):
            rule = {}
            rule["rule_tag"] = rule_tag
            rule["solution"] = stringify_children(
                                    find_first_subtag(rule_tag,"fixtext"))
            self.rules[rule_tag.attrib["id"]] = rule

    def get_results_and_outputs(self):
        for result_tag in find_subtags_recursive(self.root, "rule-result"):
            rule_id = result_tag.attrib["idref"]
            result_text = find_first_subtag(result_tag, "result").text
            self.rules[rule_id]["result"] = result_text
            self.rules[rule_id]["result_tag"] = result_tag
            self.get_stdout_stderr(rule_id, result_tag)

    def get_stdout_stderr(self, rule_id, result_tag):
        for output_tag in find_subtags_recursive(result_tag, "check-import"):
            output_type = output_tag.attrib["import-name"]
            self.rules[rule_id][output_type] = output_tag.text

    def remove_same_result_rules(self, same_result_rules):
        for rule_id in same_result_rules.keys():
            self.remove_rule(rule_id)
            del self.rules[rule_id]

    def remove_rule(self, rule_id):
        """Remove all references to a rule from the whole XML."""
        remove_tag(self.rules[rule_id]["rule_tag"])
        remove_tag(self.rules[rule_id]["result_tag"])
        remove_tag(self.get_select_tag(rule_id))

    def get_select_tag(self, rule_id):
        for select_tag in find_subtags_recursive(self.root, "select"):
            if select_tag.attrib["idref"] == rule_id:
                return select_tag
        else:
            sys.exit("Error: Can't find select tag: {0}.".format(rule_id))

    def remove_empty_group_tags(self):
        for group_tag in find_subtags_recursive(self.root, "Group"):
            if has_no_subtags_recursive(group_tag, "Rule"):
                remove_tag(group_tag)

    def write_to_file(self):
        self.tree.write(diff_report_name_xml, pretty_print=True)


"""-----------------XML UTILS-----------------"""


def get_xml_tree_object(xml_path):
    try:
        return ET.parse(xml_path)
    except:
        sys.exit("Error: Failed to parse '{0}'.\nPreupgrade Assistant result"
                 " XML expected.".format(xml_path))


def stringify_children(tag_obj):
    """
    Return body of the given node 'tag_obj'. For example, if the node contains
    following text: 'str1<br />str2<b>str3</b>str4'
    then tag_obj.text contains just 'str1' and rest of text is thrown away.
    This function returns whole text inside the given node.
    """
    s = tag_obj.text
    if s is None:
        s = ''
    else:
        s = s.encode("UTF-8")
    for child in tag_obj:
        s += ET.tostring(child, encoding="UTF-8")
    return s


def find_subtags_recursive(tag_obj, subtag_name):
    """Returns tags with the specific name within the whole XML."""
    tag_name_with_ns = get_tag_with_ns(subtag_name)
    return tag_obj.getiterator(tag_name_with_ns)


def find_first_subtag(tag_obj, subtag_name):
    tag_name_with_ns = get_tag_with_ns(subtag_name)
    return tag_obj.find(tag_name_with_ns)


def get_tag_with_ns(tag_name):
    """All the tags in Preupgrade Assistant result XML are prepended with ns0
    namespace, which is required by python XML parsing modules when
    looking for a tag. This function returns a tag name prepended by this
    namespace and the return value can be used directly for tag searches.
    """
    return "{%s}%s" % (namespace, tag_name)


def remove_tag(tag_obj):
    parent = tag_obj.getparent()
    parent.remove(tag_obj)


def has_no_subtags_recursive(tag_obj, subtag_name):
    """Return true if tag_obj has no subtags of a particular name."""
    if sum(1 for _ in find_subtags_recursive(tag_obj, subtag_name)):
        return False
    else:
        return True


def check_files_are_readable(files):
    for file in files:
        if not FileHelper.check_file(file, "r"):
            sys.exit("Error: Can't read '{0}'.".format(file))

"""-----------------END XML UTILS-----------------"""


def get_analyzed_xml_paths(cli_paths):
    """User can enter multiple XMLs and also directory in which there are
    multiple XMLs. This function returns a list of all the XMLs.
    """
    analyzed_xml_paths = []
    for path in cli_paths:
        if os.path.isfile(path):
            analyzed_xml_paths.append(path)
        elif os.path.isdir(path):
            sys.exit("Error: Detected directory on input: '{0}'."
                     " Enter an XML file instead.".format(path))
        else:
            sys.exit("Error: Can't access '{0}'.".format(path))

    if not analyzed_xml_paths:
        sys.exit("Error: No analyzed XML found.")

    check_files_are_readable(analyzed_xml_paths)

    return analyzed_xml_paths


def load_analyzed_xmls(xml_paths):
    loaded_xmls = []
    for xml_path in xml_paths:
        loaded_xml = ResultXML(xml_path)
        loaded_xmls.append(loaded_xml)
    return loaded_xmls


def get_diff_xml(analyzed_xmls, new_xml):
    # Number of rules in the new XML
    num_new_xml_rules = len(new_xml.rules.keys())

    for analyzed_xml in analyzed_xmls:
        same_result_rules = get_rules_w_same_result(analyzed_xml.rules,
                                                    new_xml.rules)
        new_xml.remove_same_result_rules(same_result_rules)

    diff_xml = new_xml
    diff_xml.remove_empty_group_tags()

    # Number of rules left in the diff xml - subset of rules from the new XML
    num_diff_xml_rules = len(new_xml.rules.keys())

    print_difference_status(num_new_xml_rules, num_diff_xml_rules)
    return diff_xml


def get_rules_w_same_result(first_xml_rules, new_xml_rules):
    same_result_rules = {}
    for rule_id in new_xml_rules.keys():
        if rule_id not in first_xml_rules:
            continue
        # Save those new XML rules that have the same result as in the old XML
        if are_results_same(first_xml_rules[rule_id],
                            new_xml_rules[rule_id]):
            same_result_rules[rule_id] = new_xml_rules[rule_id]

    return same_result_rules


def are_results_same(first_xml_rule_attrs, new_xml_rule_attrs):
    for rule_attr in rule_attrs_to_compare:
        if rule_attr not in first_xml_rule_attrs or \
                rule_attr not in new_xml_rule_attrs:
            continue
        if first_xml_rule_attrs[rule_attr] != new_xml_rule_attrs[rule_attr]:
            return False
    return True


def print_difference_status(num_new_xml_rules, num_diff_xml_rules):
    if num_diff_xml_rules:
        if num_new_xml_rules == num_diff_xml_rules:
            verbose_print("All the rules have different results. The diff XML"
                          " is the same as the new XML.")
        else:
            verbose_print("Removed %d rules (out of %d) from the new XML."
                          "\nNote: The removed rules had exactly the same"
                          " result in one of the analyzed XMLs and in the"
                          " new XML."
                          % (num_new_xml_rules - num_diff_xml_rules,
                             num_new_xml_rules))
    else:
        verbose_print("Every rule from the new XML has exactly the same"
                      " result as in at least one of the analyzed XMLs.")


def save_diff_to_xml_and_html_file(diff_xml):
    diff_xml.write_to_file()
    fix_xml_for_simple_html()
    verbose_print("Diff XML generated: " + diff_report_name_xml)
    generate_html()
    verbose_print("Diff HTML generated: " + diff_report_name_html)


def fix_xml_for_simple_html():
    """OpenSCAP requires version of XCCDF to be 1.1 in order to correctly
    generate "simple" HTML.
    """
    if not parsed_opts.simple_html:
        return
    with open(diff_report_name_xml, 'r') as infile:
        first_line = infile.readline().replace(
            namespace, namespace.replace("1.2", "1.1"))
        rest = infile.read()
    with open(diff_report_name_xml, 'w') as outfile:
        outfile.write(first_line)
        outfile.write(rest)


def verbose_print(message):
    if parsed_opts.verbose:
        print(message)


def generate_html():
    if not os.path.exists(diff_report_name_xml):
        sys.exit("Error: HTML generation failed: source {0} not found."
                 .format(diff_report_name_xml))
    cmd = OpenSCAPHelper.build_generate_command(diff_report_name_xml,
                                                diff_report_name_html,
                                                parsed_opts.simple_html)
    log = "html.log"  # log for text printed during html generation
    ret_val = ProcessHelper.run_subprocess(cmd, print_output=True,
                                           output=log)
    if ret_val != 0:
        sys.exit("Error: HTML generation failed. See {0} for details."
                 .format(log))
    else:  # no error when generating html - safe to remove the log
        os.remove(log)


def run():
    """The main entry point of the preupg-diff tool"""
    global parsed_opts
    parsed_opts = parse_cli_opts()
    analyzed_xml_paths = get_analyzed_xml_paths(parsed_opts.analyzed_xml)
    analyzed_xmls = load_analyzed_xmls(analyzed_xml_paths)
    new_xml = ResultXML(parsed_opts.new_xml)
    diff_xml = get_diff_xml(analyzed_xmls, new_xml)
    save_diff_to_xml_and_html_file(diff_xml)
