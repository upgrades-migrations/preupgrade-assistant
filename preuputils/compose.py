from __future__ import print_function
import os
import sys
import re
import datetime

import six
from distutils import dir_util

from preup.utils import get_valid_scenario, get_file_content, write_to_file
from preuputils import variables
from preuputils.oscap_group_xml import OscapGroupXml
from preup import settings
from preup import xccdf
from xml.etree import ElementTree
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError

XCCDF_FRAGMENT = "{http://fedorahosted.org/sce-community-content/wiki/XCCDF-fragment}"
SCE = "http://open-scap.org/page/SCE"


class XCCDFCompose(object):
    dir_name = ""
    result_dir = ""

    def __init__(self, argument):
        """
        Specify dirname with the on content
        :param argument: dirname where content is
        :return:
        """
        self.result_dir = argument
        self.dir_name = self.result_dir + variables.result_prefix
        if self.result_dir.endswith("/"):
            self.dir_name = self.result_dir[:-1] + variables.result_prefix

        if get_valid_scenario(self.dir_name) is None:
            print ('Use valid scenario like RHEL6_7 or CENTOS6_RHEL6')
            sys.exit(1)

    def generate_xml(self):
        dir_util.copy_tree(self.result_dir, self.dir_name)
        result_dirname = self.dir_name
        template_file = ComposeXML.get_template_file()
        try:
            target_tree = ElementTree.parse(template_file).getroot()
        except IOError as e:
            print ('Problem with reading template.xml file')
            sys.exit(1)
        target_tree = ComposeXML.run_compose(target_tree, self.dir_name)

        report_filename = os.path.join(result_dirname, settings.content_file)
        try:
            write_to_file(report_filename, "w",
                          ElementTree.tostring(target_tree, "utf-8"),
                          False)
            print ('Generate report file for preupgrade-assistant is:', ''.join(report_filename))
        except IOError as e:
            print ("Problem with writing file ", report_filename)
            raise
        return self.dir_name


class ComposeXML(object):

    upgrade_path = ""

    @classmethod
    def collect_group_xmls(cls, source_dir, content=None, level=0):
        ret = {}

        for dirname in os.listdir(source_dir):
            if content and dirname != content:
                continue
            if dirname and dirname[0] == '.':
                continue
            new_dir = os.path.join(source_dir, dirname)
            if not os.path.isdir(new_dir):
                continue
            ini_files = filter(lambda x: x.endswith(".ini"), os.listdir(new_dir))
            if ini_files:
                oscap_group = OscapGroupXml(new_dir)
                oscap_group.write_xml()
                return_list = oscap_group.collect_group_xmls()
                cls.perform_autoqa(new_dir, return_list)

            group_file_path = os.path.join(new_dir, "group.xml")
            if not os.path.isfile(group_file_path):
                # print("Directory '%s' is missing a group.xml file!" % (new_dir))
                continue
            try:
                ret[dirname] = (ElementTree.parse(group_file_path).getroot(),
                                cls.collect_group_xmls(new_dir, level=level + 1))
            except ParseError as e:
                print ("Encountered a parse error in file ", group_file_path, " details: ", e)
        return ret

    @classmethod
    def perform_autoqa(cls, path_prefix, group_tree):
        for f, t in six.iteritems(group_tree):
            b_subgroups = True
            try:
                tree, subgroups = t
            except ValueError:
                tree = t
                b_subgroups = False

            group_xml_path = os.path.join(f, "group.xml")

            groups = tree.findall(xccdf.XMLNS + "Group")
            if len(groups) != 1:
                """print("'%s' doesn't have exactly one Group element."
                      " Each group.xml file is allowed to have just one group in it, "
                      "if you want to split a group into two, "
                      "move the other half to a different folder!" % (group_xml_path))
                """
                continue

            for element in tree.findall(".//" + xccdf.XMLNS + "Rule"):
                checks = element.findall(xccdf.XMLNS + "check")
                if len(checks) != 1:
                    print ("Rule of id ", element.get("id", ""),
                           " from ", group_xml_path,
                           " doesn't have exactly one check element!")
                    continue

                check = checks[0]

                if check.get("system") != SCE:
                    print ("Rule of id '", element.get("id", ""),
                           "' from ", group_xml_path, " has system name different from the SCE system name ",
                           "('", SCE, "')!")

                crefs = check.findall(xccdf.XMLNS + "check-content-ref")
                if len(crefs) != 1:
                    print("Rule of id '", element.get("id", ""),
                          "' from '", group_xml_path,
                          "' doesn't have exactly one check-content-ref inside its check element!")
                    continue

                cref = crefs[0]

                # Check if the description contains a list of affected files
                description = element.find(xccdf.XMLNS + "description")
                if description is None:
                    print ("Rule ", element.get("id", ""), " missing a description")
                    continue

            if b_subgroups:
                cls.perform_autoqa(os.path.join(path_prefix, f), subgroups)

    @classmethod
    def repath_group_xml_tree(cls, source_dir, new_base_dir, group_tree):
        for f, t in six.iteritems(group_tree):
            tree, subgroups = t

            old_base_dir = os.path.join(source_dir, f)

            path_prefix = os.path.relpath(old_base_dir, new_base_dir)
            for element in tree.findall(".//" + xccdf.XMLNS + "check-content-ref"):
                old_href = element.get("href")
                assert(old_href is not None)
                element.set("href", os.path.join(path_prefix, old_href))

            cls.repath_group_xml_tree(old_base_dir, new_base_dir, subgroups)

    @classmethod
    def merge_trees(cls, target_tree, target_element, group_tree):
        def get_sorting_key_for_tree(group_tree, tree_key):
            prefix = 100
            tree, subgroups = group_tree[tree_key]
            try:
                prefix = int(tree.findall(XCCDF_FRAGMENT + "sort-prefix")[-1].text)
            except:
                pass

            return prefix, tree_key

        for f in sorted(six.iterkeys(group_tree), key=lambda tree_key: get_sorting_key_for_tree(group_tree, tree_key)):
            t = group_tree[f]
            tree, subgroups = t

            groups = tree.findall(xccdf.XMLNS + "Group")
            if len(groups) != 1:
                print("There are %i groups in '%s/group.xml' file. Exactly 1 group is expected! Skipping..." % (len(groups), f))
                continue
            target_element.append(groups[0])
            for child in tree.findall(xccdf.XMLNS + "Profile"):
                assert(child.get("id") is not None)
                merged = False

                # look through profiles in the template XCCDF
                for profile in target_tree.findall(xccdf.XMLNS + "Profile"):
                    if profile.get("id") == child.get("id"):
                        for profile_child in child.findall("*"):
                            profile.append(profile_child)

                        merged = True
                        break

                if not merged:
                    print("Found profile of id '%s' that doesn't match any profiles in template, skipped!" % (child.get("id")), sys.stderr)

            cls.merge_trees(target_tree, groups[0], subgroups)

    @classmethod
    def resolve_selects(cls, target_tree):
        default_selected_rules = set([])
        all_rules = set([])

        for profile in target_tree.findall(xccdf.XMLNS + "Profile"):
            selected_rules = set(default_selected_rules)

            # to avoid invalidating iterators
            to_remove = []
            for select in profile.findall("*"):

                if select.tag == xccdf.XMLNS + "select":
                    if select.get("selected", "false") == "true":
                        selected_rules.add(select.get("idref", ""))
                    else:
                        selected_rules.remove(select.get("idref", ""))

                    to_remove.append(select)

                elif select.tag == XCCDF_FRAGMENT + "meta-select":
                    needle = select.get("idref")
                    for rule_id in all_rules:
                        if re.match(needle, rule_id):
                            if select.get("selected", "false") == "true":
                                selected_rules.add(rule_id)
                            elif rule_id in selected_rules:
                                selected_rules.remove(rule_id)

                    to_remove.append(select)

            for rm in to_remove:
                profile.remove(rm)

            for rule in selected_rules:
                # if it's selected by default, we don't care
                if rule not in default_selected_rules:
                    elem = ElementTree.Element(xccdf.XMLNS + "select")
                    elem.set("idref", rule)
                    elem.set("selected", "true")
                    profile.append(elem)

            for rule in default_selected_rules:
                if rule not in selected_rules:
                    elem = ElementTree.Element(xccdf.XMLNS + "select")
                    elem.set("idref", rule)
                    elem.set("selected", "false")
                    profile.append(elem)

    @classmethod
    def update_content_ref(cls, target_tree, content):
        if not content:
            return target_tree
        for content_ref in target_tree.findall(".//" + xccdf.XMLNS + "check"):
            for check_ref in content_ref.findall("*"):
                if check_ref.tag == xccdf.XMLNS + "check-content-ref":
                    reference = check_ref.get("href")
                    check_ref.set("href", os.path.basename(reference))

        return target_tree

    @classmethod
    def refresh_status(cls, target_tree):
        for status in target_tree.findall(xccdf.XMLNS + "status"):
            if status.get("date", "") == "${CURRENT_DATE}":
                status.set("date", datetime.date.today().strftime("%Y-%m-%d"))

    # taken from http://effbot.org/zone/element-lib.htm#prettyprint
    @classmethod
    def indent(cls, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                cls.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    @classmethod
    def get_template_file(cls):
        return os.path.join(os.path.dirname(__file__), "template.xml")

    @classmethod
    def run_compose(cls, target_tree, dir_name, content=None):
        settings.UPGRADE_PATH = dir_name
        group_xmls = cls.collect_group_xmls(dir_name, content=content, level=0)
        cls.perform_autoqa(dir_name, group_xmls)
        new_base_dir = dir_name
        cls.repath_group_xml_tree(dir_name, new_base_dir, group_xmls)
        cls.merge_trees(target_tree, target_tree, group_xmls)
        target_tree = cls.update_content_ref(target_tree, content)
        cls.resolve_selects(target_tree)
        cls.refresh_status(target_tree)
        cls.indent(target_tree)

        return target_tree

