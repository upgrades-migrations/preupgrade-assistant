from __future__ import print_function, unicode_literals
import os
import sys
import re
import datetime
import shutil

from distutils import dir_util

from preupg.utils import FileHelper, ModuleSetUtils
from preupg.xmlgen.oscap_group_xml import OscapGroupXml
from preupg import settings
from preupg import xccdf
from preupg.logger import logger_debug
from preupg.settings import ReturnValues
from preupg.logger import log_message, logging

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError

XCCDF_FRAGMENT = "{http://fedorahosted.org/sce-community-content/wiki/" \
                 "XCCDF-fragment}"
SCE = "http://open-scap.org/page/SCE"


class XCCDFCompose(object):
    """
    Prepare result directory and take care of creating all-xccdf.xml file
    """

    def __init__(self, src_path, dst_path=None):
        """
        Create the XCCDFCompose object with specified src and dst path.

        The src_path specify source modules from which the XCCDF compose should
        be created on the dst_path. In case the dst_path is not specified, the
        result directory will be created, in the same place the source directory
        exists, with the "-results" suffix using the original dirname.

        src_path and dst_path has to be different, otherwise ValueError
        exception is raised.
        """
        self.src_path = src_path
        if not dst_path:
            self.dst_path = self.src_path + settings.results_postfix
            if self.src_path.endswith("/"):
                self.dst_path = self.src_path[:-1] + settings.results_postfix
        else:
            self.dst_path = dst_path
        if self.dst_path == self.src_path:
            raise ValueError("src_path and dst_path has to be different.")

        # Delete previous contents if they exist.
        if os.path.exists(self.dst_path):
            shutil.rmtree(self.dst_path)

    def generate_xml(self, generate_from_ini=True):
        """
        Copy files to result directory and if specified generate all-xccdf.xml
        file

        @param {bool} generate_from_ini - True if xccdf-compose tool is used,
            decide if all-xccdf.xml file will(True) be created or not(False)
        @throws {IOError} - when creation of all-xccdf.xml file fails
        @return {int} - 0 success
                       !0 error
        """
        try:
            ModuleSetUtils.get_module_set_os_versions(self.src_path)
        except EnvironmentError as err:
            sys.stderr.write("{0}\n".format(str(err)))
            return ReturnValues.SCENARIO

        # e.g. /root/preupgrade/RHEL6_7 -> /root/preupgrade/RHEL6_7-results
        dir_util.copy_tree(self.src_path, self.dst_path)
        # create content for all-xccdf.xml file as ElementTree object
        target_tree = ComposeXML.run_compose(
            self.dst_path, generate_from_ini=generate_from_ini)
        # path where all-xccdf.xml is going to be generated
        report_filename = os.path.join(self.dst_path,
                                       settings.all_xccdf_xml_filename)
        if generate_from_ini:
            try:
                FileHelper.write_to_file(
                    report_filename, "wb",
                    ElementTree.tostring(target_tree, "utf-8"), False
                )
                logger_debug.debug('Generated: %s' % report_filename)
            except IOError:
                raise IOError("Error: Problem with writing file %s"
                              % report_filename)
        return 0

    def get_compose_dir_name(self):
        return self.dst_path


class ComposeXML(object):

    @staticmethod
    def collect_group_xmls(module_set_dir, source_dir, generate_from_ini=True):
        """
        Find group.xml file recursively through all module directories
        and modules. Collect data from each of them into dictionary.

        @param {str} module_set_dir - directory where all modules are stored
        @param {str} source_dir - directory path for processing
        @param {bool} generate_from_ini - True if xccdf-compose tool is used

        @return {dict} - structure is file based, keys are top level module
        directories, values are tuples which consist of 2 elements:
            [0] - XML data for top level dir itself
            [1] - dict of all modules inside [0] directory
        @example
        from file structure:
            - RHEL6_7
                - services (modules directory)
                    - group.xml
                    - group.ini
                    - httpd (module)
                        - group.xml
                        - ...
                    - tomcat (module)
                        - group.xml
                        - ...
                - drivers (modules directory)
                - ...
        result is:
            {
                services: tuple(
                    <Element {services}>,
                    {
                        httpd: tuple(<Element {httpd}>, {}),
                        tomcat: tuple(<Element {tomcat}>, {}),
                        ...
                    }
                ),
                drivers: tuple(
                    <Element {drivers}>,
                    {...}
                ),
                ...
            }
        """
        ret = {}

        for dirname in os.listdir(source_dir):
            if dirname and dirname[0] == '.':
                continue
            new_dir = os.path.join(source_dir, dirname)
            if not os.path.isdir(new_dir):
                continue
            ini_files = [x for x in os.listdir(new_dir) if x.endswith('.ini')]
            if not ini_files and generate_from_ini:
                # Check if directory contains only subdirectories.
                # Report to user that group.ini file could be missing
                directories = [x for x in os.listdir(new_dir)
                               if not os.path.isdir(os.path.join(new_dir, x))]
                if not directories and 'postupgrade.d' not in dirname:
                    log_message(
                        "group.ini file is missing in {0}".format(new_dir),
                        level=logging.WARNING)
            if ini_files and generate_from_ini:
                oscap_group = OscapGroupXml(module_set_dir, new_dir)
                oscap_group.write_xml()
                return_list = oscap_group.collect_group_xmls()
                ComposeXML.perform_autoqa(new_dir, return_list)

            group_file_path = os.path.join(new_dir, "group.xml")
            if not os.path.isfile(group_file_path):
                continue
            try:
                ret[dirname] = (ElementTree.parse(group_file_path).getroot(),
                                ComposeXML.collect_group_xmls(
                                    module_set_dir, new_dir,
                                    generate_from_ini))
            except ParseError as e:
                log_message(
                    "Encountered a parse error in {0} file, details: {1}"
                    .format(group_file_path, e), level=logging.ERROR)
                sys.exit(1)
        return ret

    @staticmethod
    def perform_autoqa(path_prefix, group_tree):
        for f, t in iter(group_tree.items()):
            b_subgroups = True
            try:
                tree, subgroups = t
            except ValueError:
                tree = t
                b_subgroups = False

            group_xml_path = os.path.join(f, "group.xml")

            groups = tree.findall(xccdf.XMLNS + "Group")
            if len(groups) != 1:
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
                           "' from ", group_xml_path, " has system name"
                           " different from the SCE system name ",
                           "('", SCE, "')!")

                crefs = check.findall(xccdf.XMLNS + "check-content-ref")
                if len(crefs) != 1:
                    print("Rule of id '", element.get("id", ""),
                          "' from '", group_xml_path,
                          "' doesn't have exactly one check-content-ref inside"
                          " its check element!")
                    continue

                # Check if the description contains a list of affected files
                description = element.find(xccdf.XMLNS + "description")
                if description is None:
                    print ("Rule ", element.get("id", ""),
                           " missing a description")
                    continue

            if b_subgroups:
                ComposeXML.perform_autoqa(os.path.join(path_prefix, f),
                                          subgroups)

    @staticmethod
    def repath_group_xml_tree(source_dir, new_base_dir, group_tree):
        """
        Fix href attribute inside <check-content-ref> for each
        XML Element module

        @param {str} source_dir - directory where module is located e.g.
            /root/preupgrade/RHEL6_7-results/backup/bacula
        @param {str} new_base_dir - base directory e.g.
            /root/preupgrade/RHEL6_7-results
        @param {dict} group_tree - if source_dir is module set directory it
            has all modules which are inside this directory, e.g.
            source_dir: /root/preupgrade/RHEL6_7-results/backup
            group_tree: {bacula: (<Element {bacula}>, {})}

        @return None

        @example
        from:
            <ns0:check-content-ref href="check" />
        to:
            <ns0:check-content-ref href="backup/bacula/check" />
        """
        for f, t in iter(group_tree.items()):
            tree, subgroups = t

            old_base_dir = os.path.join(source_dir, f)

            path_prefix = os.path.relpath(old_base_dir, new_base_dir)
            for element in tree.findall(".//" + xccdf.XMLNS +
                                        "check-content-ref"):
                old_href = element.get("href")
                assert(old_href is not None)
                element.set("href", os.path.join(path_prefix, old_href))

            ComposeXML.repath_group_xml_tree(old_base_dir, new_base_dir,
                                             subgroups)

    @staticmethod
    def merge_trees(target_tree, target_element, group_tree):
        def get_sorting_key_for_tree(group_tree, tree_key):
            prefix = 100
            tree, dummy_subgroups = group_tree[tree_key]
            try:
                prefix = int(tree.findall(XCCDF_FRAGMENT + "sort-prefix")
                             [-1].text)
            except:
                pass

            return prefix, tree_key

        def sort_key(t_key):
            return get_sorting_key_for_tree(group_tree, t_key)

        for f in sorted(iter(group_tree.keys()), key=sort_key):
            t = group_tree[f]
            tree, subgroups = t

            groups = tree.findall(xccdf.XMLNS + "Group")
            if len(groups) != 1:
                print("There are %i groups in '%s/group.xml' file. Exactly 1"
                      " group is expected! Skipping..." % (len(groups), f))
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
                    print("Found profile of id '%s' that doesn't match any"
                          " profiles in template, skipped!"
                          % (child.get("id")), sys.stderr)

            ComposeXML.merge_trees(target_tree, groups[0], subgroups)

    @staticmethod
    def resolve_selects(target_tree):
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

    @staticmethod
    def refresh_status(target_tree):
        for status in target_tree.findall(xccdf.XMLNS + "status"):
            if status.get("date", "") == "${CURRENT_DATE}":
                status.set("date", datetime.date.today().strftime("%Y-%m-%d"))

    # taken from http://effbot.org/zone/element-lib.htm#prettyprint
    @staticmethod
    def indent(elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                ComposeXML.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    @staticmethod
    def get_template_file():
        return os.path.join(settings.data_dir, "templates",
                            settings.xccdf_template)

    @staticmethod
    def get_xml_tree():
        template_file = ComposeXML.get_template_file()
        try:
            target_tree = ElementTree.parse(template_file).getroot()
        except IOError:
            raise IOError('Error: Problem with reading %s file'
                          % template_file)
        return target_tree

    @staticmethod
    def run_compose(dir_name, generate_from_ini=True):
        target_tree = ComposeXML.get_xml_tree()
        settings.UPGRADE_PATH = dir_name
        if os.path.exists(os.path.join(dir_name, settings.file_list_rules)):
            os.unlink(os.path.join(dir_name, settings.file_list_rules))
        group_xmls = ComposeXML.collect_group_xmls(dir_name, dir_name,
                                                   generate_from_ini)
        logger_debug.debug("Group xmls '%s'", group_xmls)
        if generate_from_ini:
            ComposeXML.perform_autoqa(dir_name, group_xmls)
        new_base_dir = dir_name
        ComposeXML.repath_group_xml_tree(dir_name, new_base_dir, group_xmls)
        ComposeXML.merge_trees(target_tree, target_tree, group_xmls)
        ComposeXML.resolve_selects(target_tree)
        ComposeXML.refresh_status(target_tree)
        ComposeXML.indent(target_tree)

        return target_tree
