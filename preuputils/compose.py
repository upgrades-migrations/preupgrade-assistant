import os
import sys
import re
import datetime

from preuputils.oscap_group_xml import OscapGroupXml
from preuputils.generate_xml import GenerateXml
from xml.etree import ElementTree
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError

XMLNS = "{http://checklists.nist.gov/xccdf/1.2}"


def collect_group_xmls(source_dir, level=0):
    ret = {}

    for dirname in os.listdir(source_dir):
        if dirname and dirname[0] == '.':
            continue
        if not os.path.isdir(os.path.join(source_dir, dirname)):
            continue
        ini_files = filter(lambda x: x.endswith(".ini"), os.listdir(os.path.join(source_dir, dirname)))
        if ini_files:
            oscap_group = OscapGroupXml(source_dir+"/"+dirname)
            oscap_group.write_xml()
            return_list = oscap_group.collect_group_xmls()
            generate_xml = GenerateXml(source_dir+"/"+dirname, True, return_list)
            generate_xml.make_xml()
        group_file_path = os.path.join(source_dir, dirname, "group.xml")
        if not os.path.isfile(group_file_path):
            #print("Directory '%s' is missing a group.xml file!" % (os.path.join(source_dir, dirname)))
            continue
        with open(group_file_path, "r") as file:
            try:
                ret[dirname] = (ElementTree.fromstring(file.read()),
                                collect_group_xmls(os.path.join(source_dir, dirname),
                                level=level + 1))
            except ParseError as e:
                print("Encountered a parse error in file '%s', details: %s" % (group_file_path, e))
    return ret


def perform_autoqa(path_prefix, group_tree):
    for f, t in group_tree.iteritems():
        tree, subgroups = t

        group_xml_path = os.path.join(f, "group.xml")

        groups = tree.findall(XMLNS + "Group")
        if len(groups) != 1:
            print("'%s' doesn't have exactly one Group element."
                  " Each group.xml file is allowed to have just one group in it, "
                  "if you want to split a group into two, "
                  "move the other half to a different folder!" % (group_xml_path))
            continue

        for element in tree.findall(".//" + XMLNS + "Rule"):
            checks = element.findall(XMLNS + "check")
            if len(checks) != 1:
                print("Rule of id '%s' from '%s' doesn't have "
                      "exactly one check element!" % (element.get("id", ""), group_xml_path))
                continue

            check = checks[0]

            if check.get("system") != "http://open-scap.org/page/SCE":
                print("Rule of id '%s' from '%s' has system name different "
                      "from the SCE system name "
                      "('http://open-scap.org/page/SCE')!" % (element.get("id", ""), group_xml_path))

            crefs = check.findall(XMLNS + "check-content-ref")
            if len(crefs) != 1:
                print("Rule of id '%s' from '%s' doesn't have exactly one "
                      "check-content-ref inside its check element!" % (element.get("id", ""), group_xml_path))
                continue

            cref = crefs[0]

            # Check if the description contains a list of affected files
            description = element.find(XMLNS + "description")
            if description is None:
                print("Rule %r missing a description" % element.get("id", ""))
                continue

        perform_autoqa(os.path.join(path_prefix, f), subgroups)


def repath_group_xml_tree(source_dir, new_base_dir, group_tree):
    for f, t in group_tree.iteritems():
        tree, subgroups = t

        old_base_dir = os.path.join(source_dir, f)

        path_prefix = os.path.relpath(old_base_dir, new_base_dir)
        for element in tree.findall(".//" + XMLNS + "check-content-ref"):
            old_href = element.get("href")
            assert(old_href is not None)
            element.set("href", os.path.join(path_prefix, old_href))

        repath_group_xml_tree(old_base_dir, new_base_dir, subgroups)


def merge_trees(target_tree, target_element, group_tree):
    def get_sorting_key_for_tree(group_tree, tree_key):
        prefix = 100
        tree, subgroups = group_tree[tree_key]
        try:
            prefix = int(tree.findall("{http://preupgrade-assistant.org/wiki/XCCDF-fragment}sort-prefix")[-1].text)
        except:
            pass

        return prefix, tree_key

    for f in sorted(group_tree.iterkeys(), key = lambda tree_key: get_sorting_key_for_tree(group_tree, tree_key)):
        t = group_tree[f]
        tree, subgroups = t

        groups = tree.findall(XMLNS + "Group")
        if len(groups) != 1:
            print("There are %i groups in '%s/group.xml' file. Exactly 1 group is expected! Skipping..." % (len(groups), f))
            continue
        target_element.append(groups[0])
        for child in tree.findall(XMLNS + "Profile"):
            assert(child.get("id") is not None)
            merged = False

            # look through profiles in the template XCCDF
            for profile in target_tree.findall(XMLNS + "Profile"):
                if profile.get("id") == child.get("id"):
                    for profile_child in child.findall("*"):
                        profile.append(profile_child)

                    merged = True
                    break

            if not merged:
                print("Found profile of id '%s' that doesn't match any profiles in template, skipped!" % (child.get("id")), sys.stderr)

        merge_trees(target_tree, groups[0], subgroups)


def resolve_selects(target_tree):
    default_selected_rules = set([])
    all_rules = set([])

    for profile in target_tree.findall(XMLNS + "Profile"):
        selected_rules = set(default_selected_rules)

        to_remove = [] # to avoid invalidating iterators
        for select in profile.findall("*"):

            if select.tag == XMLNS + "select":
                if select.get("selected", "false") == "true":
                    selected_rules.add(select.get("idref", ""))
                else:
                    selected_rules.remove(select.get("idref", ""))

                to_remove.append(select)

            elif select.tag == "{http://preupgrade-assistant.org/wiki/XCCDF-fragment}meta-select":
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
            if rule not in default_selected_rules: # if it's selected by default, we don't care
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


def refresh_status(target_tree):
    for status in target_tree.findall(XMLNS + "status"):
        if status.get("date", "") == "${CURRENT_DATE}":
            status.set("date", datetime.date.today().strftime("%Y-%m-%d"))


# taken from http://effbot.org/zone/element-lib.htm#prettyprint
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def get_template_file():
    return os.path.join(os.path.dirname(__file__), "template.xml")


def run_compose(target_tree, dir_name):
    group_xmls = collect_group_xmls(dir_name, level=0)
    perform_autoqa(dir_name, group_xmls)
    new_base_dir = dir_name
    repath_group_xml_tree(dir_name, new_base_dir, group_xmls)
    merge_trees(target_tree, target_tree, group_xmls)
    resolve_selects(target_tree)
    refresh_status(target_tree)

    indent(target_tree)

    return target_tree

