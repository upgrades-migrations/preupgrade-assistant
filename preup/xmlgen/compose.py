from __future__ import print_function, unicode_literals
import os
import sys
import re
import datetime
import shutil

import six
from distutils import dir_util

from preup.utils import FileHelper, SystemIdentification
from preup.xmlgen.oscap_group_xml import OscapGroupXml
from preup import settings
from preup import xccdf
from preup.logger import logger_debug
from preup.settings import ReturnValues

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
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
        self.dir_name = self.result_dir + settings.results_postfix
        if self.result_dir.endswith("/"):
            self.dir_name = self.result_dir[:-1] + settings.results_postfix

        # Delete previous contents if they exist.
        if os.path.exists(self.dir_name):
            shutil.rmtree(self.dir_name)

    def generate_xml(self, generate_from_ini=True):
        if SystemIdentification.get_valid_scenario(self.dir_name) is None:
            print ('Use valid scenario like RHEL6_7 or CENTOS6_RHEL6')
            return ReturnValues.SCENARIO

        dir_util.copy_tree(self.result_dir, self.dir_name)
        target_tree = ComposeXML.run_compose(self.dir_name, generate_from_ini=generate_from_ini)

        report_filename = os.path.join(self.dir_name, settings.content_file)
        try:
            FileHelper.write_to_file(report_filename, "wb",
                                     ElementTree.tostring(target_tree, "utf-8"),
                                     False)
            if generate_from_ini:
                print ('Generate report file for preupgrade-assistant is:', ''.join(report_filename))
        except IOError:
            print ("Problem with writing file ", report_filename)
            raise
        return 0

    def get_compose_dir_name(self):
        return self.dir_name


class ComposeXML(object):

    upgrade_path = ""

    @classmethod
    def collect_group_xmls(cls, source_dir, content=None, level=0, generate_from_ini=True):
        ret = {}

        for dirname in os.listdir(source_dir):
            if content and dirname != content:
                continue
            if dirname and dirname[0] == '.':
                continue
            new_dir = os.path.join(source_dir, dirname)
            if not os.path.isdir(new_dir):
                continue
            ini_files = [x for x in os.listdir(new_dir) if x.endswith('.ini')]
            if not ini_files and generate_from_ini:
                # Check if directory contains only subdirectories.
                # Report to user that group.ini file could be missing
                directories = [x for x in os.listdir(new_dir) if not os.path.isdir(os.path.join(new_dir, x))]
                if not directories and 'postupgrade.d' not in dirname:
                    print ("WARNING: It seems that group.ini file is missing %s. Please check if it is really missing." % new_dir)
            if ini_files and generate_from_ini:
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
                                cls.collect_group_xmls(new_dir, level=level + 1, generate_from_ini=generate_from_ini))
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

                # cref = crefs[0]

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
            tree, dummy_subgroups = group_tree[tree_key]
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
        return os.path.join(settings.data_dir, "templates",
                            settings.xccdf_template)

    @classmethod
    def get_xml_tree(cls):
        template_file = ComposeXML.get_template_file()
        try:
            target_tree = ElementTree.parse(template_file).getroot()
        except IOError:
            print('Problem with reading {0} file'
                  .format(settings.xccdf_template))
            return None
        return target_tree

    @classmethod
    def run_compose(cls, dir_name, content=None, generate_from_ini=True):
        target_tree = ComposeXML.get_xml_tree()
        settings.UPGRADE_PATH = dir_name
        if os.path.exists(os.path.join(dir_name, settings.file_list_rules)):
            os.unlink(os.path.join(dir_name, settings.file_list_rules))
        group_xmls = cls.collect_group_xmls(dir_name, content=content, level=0, generate_from_ini=generate_from_ini)
        logger_debug.debug("Group xmls '%s'", group_xmls)
        if generate_from_ini:
            cls.perform_autoqa(dir_name, group_xmls)
        new_base_dir = dir_name
        cls.repath_group_xml_tree(dir_name, new_base_dir, group_xmls)
        cls.merge_trees(target_tree, target_tree, group_xmls)
        target_tree = cls.update_content_ref(target_tree, content)
        cls.resolve_selects(target_tree)
        cls.refresh_status(target_tree)
        cls.indent(target_tree)

        return target_tree
