import os
import xml_tags
import datetime
import re
import sys
from script_utils import get_file_content
from xml.etree import ElementTree
from preup.xccdf import XMLNS

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError

XCCDF_Fragment = "{http://fedorahosted.org/sce-community-content/wiki/XCCDF-fragment}"
SCE = "http://open-scap.org/page/SCE"


class GenerateXml(object):
    """
    Class for generation XML document from INI files
    """
    def __init__(self, dir_name, group, ret):
        self.target_tree = {}
        self.rule = []
        self.dirname = dir_name
        self.ret = ret
        self.group = group

    def perform_autoqa(self):
        """
        Function performs a AutoQA on the base of target_tree
        """
        for file_name, tree_part in self.ret.iteritems():
            tree = tree_part
            group_xml_path = os.path.join(self.dirname, "group.xml")
            groups = tree.findall(XMLNS + "Group")
            if len(groups) != 1:
                print ("'%s' doesn't have exactly one Group element."
                       "Each group.xml file is allowed to have just one group in it, "
                       "if you want to split a group into two, "
                       "move the other half to a different folder!" % group_xml_path)
                continue
            group = groups[0]

            for element in tree.findall(".//" + XMLNS + "Rule"):
                checks = element.findall(XMLNS + "check")
                if len(checks) != 1:
                    print ("Rule of id '%s' from '%s' doesn't have exactly one "
                           "check element!" % (element.get("id", ""), group_xml_path))
                    continue
                check = checks[0]
                if check.get("system") != SCE:
                    print ("Rule of id '%s' from '%s' has system name different "
                          "from the SCE system name "
                          "('" + SCE + "')!" % (element.get("id", ""),
                                                                  group_xml_path))
                crefs = check.findall(XMLNS + "check-content-ref")
                if len(crefs) != 1:
                    print ("Rule of id '%s' from '%s' doesn't have exactly "
                           "one check-content-ref inside its check "
                           "element!" % (element.get("id", ""), group_xml_path))
                    continue
                cref = crefs[0]

                description = element.find(XMLNS + "description")
                if description is None:
                    print "Rule %r missing a description" % element.get("id", "")
                    continue

    def get_sorting_key_for_tree(self, tree_key):
        prefix = 100
        tree = self.ret[tree_key]
        try:
            prefix = int(tree.findall(XCCDF_Fragment + "sort-prefix")[-1].text)
        except:
            pass
        return prefix, tree_key

    def merge_trees(self):
        """
        Function merge tree with template.xml file
        """
        content = get_file_content(os.path.join(os.path.dirname(__file__), "template.xml"), "r")
        self.target_tree = ElementTree.fromstring(content)
        for file_name in sorted(self.ret.iterkeys(), key=lambda tree_key: self.get_sorting_key_for_tree(tree_key)):
            tree_part = self.ret[file_name]
            tree = tree_part
            groups = tree.findall(XMLNS + "Group")
            if len(groups) != 1:
                print("There are %i groups in '%s/group.xml' file. "
                      "Exactly 1 group is expected! Skipping..." % (len(groups),
                                                                    file_name))
                continue
            self.target_tree.append(groups[0])
            for child in tree.findall(XMLNS + "Profile"):
                assert(child.get("id") is not None)
                merged = False
                # look through profiles in the template XCCDF
                for profile in self.target_tree.findall(XMLNS + "Profile"):
                    if profile.get("id") == child.get("id"):
                        for profile_child in child.findall("*"):
                            profile.append(profile_child)
                        merged = True
                        break
                if not merged:
                    print("Found profile of id '%s' that doesn't match "
                          "any profiles in template, skipped!" % (child.get("id")),
                          sys.stderr)

    def resolve_selects(self):
        """
        Function resolves a rules for a profile
        """
        default_selected_rules = set([])
        all_rules = set([])
        for rule in self.target_tree.findall(".//" + XMLNS + "Rule"):
            if rule.get("selected", False):
                default_selected_rules.add(rule.get("id", ""))
            all_rules.add(rule.get("id", ""))
        for profile in self.target_tree.findall(XMLNS + "Profile"):
            selected_rules = set(default_selected_rules)
            to_remove = [] # to avoid invalidating iterators
            for select in profile.findall("*"):
                if select.tag == XMLNS + "select":
                    if select.get("selected", "false") == "true":
                        selected_rules.add(select.get("idref", ""))
                    else:
                        selected_rules.remove(select.get("idref", ""))
                    to_remove.append(select)
                elif select.tag == XCCDF_Fragment + "meta-select":
                    needle = select.get("idref")
                    for rule_id in all_rules:
                        if re.match(needle, rule_id):
                            if select.get("selected", "false") == "true":
                                selected_rules.add(rule_id)
                            elif rule_id in selected_rules:
                                selected_rules.remove(rule_id)
                    to_remove.append(select)
            for rm_rule in to_remove:
                profile.remove(rm_rule)
            for rule in selected_rules:
                # if it's selected by default, we don't care
                if rule not in default_selected_rules:
                    elem = ElementTree.Element(XMLNS + "select")
                    elem.set("idref", rule)
                    elem.set("selected", "true")
                    profile.append(elem)
            for rule in default_selected_rules:
                if rule not in selected_rules:
                    elem = ElementTree.Element(XMLNS + "select")
                    elem.set("idref", rule)
                    elem.set("selected", "false")
                    profile.append(elem)

    def refresh_status(self):
        """
        Function adds a data to the tree.
        """

        for status in self.target_tree.findall(XMLNS + "status"):
            if status.get("date", "") == "${CURRENT_DATE}":
                status.set("date", datetime.date.today().strftime("%Y-%m-%d"))

    def indent(self, elem, level=0):
        """
        Function adds a indent into tree.
        """
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def make_xml(self):
        """
        Global function for making XML tree
        """
        self.perform_autoqa()
        if self.group:
            return
        self.merge_trees()
        self.resolve_selects()
        self.refresh_status()
        self.indent(self.target_tree)
        return self.target_tree
