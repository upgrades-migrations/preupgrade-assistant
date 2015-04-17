import re
import os
import collections
import six

from preup.utils import get_file_content, write_to_file
from preup import xccdf, utils
from xml.etree import ElementTree


def get_node(tree, tag, name_space='', prefix=''):
    return tree.find(prefix + name_space + tag)


def remove_node(tree, tag):
    return tree.remove(tag)


def update_current_dir(result_dir, scenario, value, mode):
    """
    Replaces a current dir with the new value
    """
    return value.text.replace("SCENARIO", os.path.join(result_dir, scenario))


def update_result_path(result_dir, scenario, value, mode):
    """
    Replaces a result path with the new value
    """
    return value.text.replace("SCENARIO", result_dir)


def update_migrate_value(result_dir, scenario, value, mode):
    """
    Replaces a migrate value with mode given by preupgrade-assistant command line
    """
    if not mode:
        return "1"
    if 'migrate' in mode:
        return "1"
    else:
        return "0"


def update_upgrade_value(result_dir, scenario, value, mode):
    """
    Replaces a upgrade value with mode given by preupgrade-assistant command line
    """
    if not mode:
        return "1"
    if 'upgrade' in mode:
        return "1"
    else:
        return "0"


def upd_inspection(rule):
    """
    Function updates result to needs_action in case
    of NONE, SLIGHT or MEDIUM risk
    """
    return rule.get("idref"), utils.get_needs_inspection()


def upd_action(rule):
    """
    Function updates result to needs_action in case
    of HIGH
    """
    return rule.get("idref"), utils.get_needs_action()


def upd_extreme(rule):
    """
    Function does no update result for extreme risk
    """
    return None, "fail"


class ReportParser(object):
    """
    Class manipulates with XML files created by oscap
    """
    def __init__(self, report_path):
        self.path = report_path
        self.element_prefix = "{http://checklists.nist.gov/xccdf/1.2}"
        try:
            # ElementTree.fromstring can't parse safely unicode string
            content = get_file_content(report_path, 'r', False, False)
        except IOError as ioerr:
            raise
        if not content:
            return None
        self.target_tree = ElementTree.fromstring(content)
        self.profile = "Profile"
        self.changed_results = {}
        self.output_data = []

    def filter_children(self, tree, tag):
        return self.get_nodes(tree, tag, prefix='./')

    def has_children(self, tree, tag):
        return len(self.get_nodes(tree, tag, prefix='./')) > 0

    def filter_grandchildren(self, tree, parent_tag, tag):
        return tree.findall('./%s%s/%s%s' % (self.element_prefix,
                                             parent_tag,
                                             self.element_prefix, tag))

    def get_child(self, tree, tag):
        return get_node(tree, tag, self.element_prefix, prefix='./')

    def get_nodes_attrib(self, tree, tag, attrib):
        try:
            return self.get_child(tree, tag).attrib[attrib]
        except (KeyError, AttributeError):
            return ''

    def get_nodes(self, tree, tag, prefix=''):
        return tree.findall(prefix + self.element_prefix + tag)

    def get_nodes_text(self, tree, tag):
        try:
            text = self.get_child(tree, tag).text
        except AttributeError:
            pass
        else:
            if text:
                return text.strip()
        return ''

    def reload_xml(self, path):
        """
        Function updates self.target_tree with the new path
        """
        self.path = path
        # ElementTree.fromstring can't parse safely unicode string
        content = get_file_content(self.path, 'r', False, False)
        if not content:
            return None
        self.target_tree = ElementTree.fromstring(content)

    def get_number_checks(self):
        """
        Function returns a number of checks
        who are really selected
        """
        number_checks = 0
        select_number = self.filter_grandchildren(self.target_tree, self.profile, "select")
        for sel in select_number:
            if sel.get('selected') == 'true':
                number_checks += 1
        return number_checks

    def _get_all_rules(self):
        return self.get_nodes(self.target_tree, "Rule", prefix=".//")

    def get_name_of_checks(self):
        """
        Function returns a names of rules
        """
        list_names = {}
        rule_nodes = self._get_all_rules()
        for select in self.filter_grandchildren(self.target_tree, self.profile, "select"):
            if select.get('selected', '') == 'true':
                id_ref = select.get('idref', '')
                rule = [x for x in rule_nodes if x.get('id', '') == id_ref]
                list_names[id_ref] = self.get_nodes_text(rule[0], "title")
        return list_names

    def get_all_result_rules(self):
        """
        Function returns all rul-result in TestResult xml tag
        """
        return self.filter_grandchildren(self.target_tree, "TestResult", "rule-result")

    def get_all_results(self):
        """
        Function return all results
        """
        results = []
        for rule in self.get_all_result_rules():
            results.extend(self.get_nodes(rule, "result", prefix='./'))
        return results

    def get_solution_files(self):
        """
        Function returns a dictionary with solution_files
        Format is:
        xccdf_preupg_backup_solution_file=solution.txt
        """
        dict_solution = {}
        for values in self.get_nodes(self.target_tree, "Value", prefix='.//'):
            value_id = values.get('id')
            if not value_id.endswith("_state_solution_file"):
                continue
            for value in self.get_nodes(values, "value"):
                value_id = value_id.replace('xccdf_preupg_value_', '').replace("_state_solution_file", '')
                dict_solution[value_id] = value.text
        return dict_solution

    def write_xml(self):
        """
        Function writes XML document to file
        """
        self.target_tree.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml/')
        # we really must set encoding here! and suppress it in write_to_file
        data = ElementTree.tostring(self.target_tree, "utf-8")
        write_to_file(self.path, 'wb', data, False)
        self.target_tree = ElementTree.parse(self.path).getroot()

    def modify_result_path(self, result_dir, scenario, mode):
        """
        Function modifies result path in XML file
        """
        update_tags = {'_tmp_preupgrade': update_result_path,
                       '_current_dir': update_current_dir,
                       '_migrate': update_migrate_value,
                       '_upgrade': update_upgrade_value}
        for key, val in update_tags.items():
            for values in self.get_nodes(self.target_tree, "Value", prefix='.//'):
                if key not in values.get('id'):
                    continue
                for value in self.get_nodes(values, "value"):
                    value.text = update_tags[key](result_dir, scenario, value, mode)

        self.write_xml()

    def modify_platform_tag(self, platform_tag):
        """
        The function updates platform tag to the assessment system tag
        """
        for platform in self.filter_children(self.target_tree, "platform"):
            if "cpe:/o:redhat:enterprise_linux:" in platform.get("idref"):
                platform.set("idref", "cpe:/o:redhat:enterprise_linux:"+platform_tag)

        self.write_xml()

    def update_inplace_risk(self, scanning_progress, rule, res):
        """
        Function updates inplace risk
        """
        inplace_risk = xccdf.get_check_import_inplace_risk(rule)
        if inplace_risk:
            return_value = xccdf.get_and_print_inplace_risk(0, inplace_risk)
            if int(return_value) < 3:
                res.text = utils.get_needs_inspection()
            elif int(return_value) == 3:
                res.text = utils.get_needs_action()
            for index, row in enumerate(scanning_progress.output_data):
                if self.get_nodes_text(rule, "title") in row:
                    scanning_progress.output_data[index] = "{0}:{1}".format(
                        self.get_nodes_text(rule, "title"),
                        res.text)

    def replace_inplace_risk(self, scanning_results=None):
        """
        This function has aim to replace FAILED to
        NEEDS_INSPECTION in case that risks are NONE or SLIGHT
        """
        #Filter all rule-result in TestResult
        changed_fields = []
        self.remove_empty_check_import()
        inplace_dict = {
            0: upd_inspection,
            1: upd_inspection,
            2: upd_inspection,
            3: upd_action,
            4: upd_extreme,
        }
        for rule in self.get_all_result_rules():
            result = [x for x in self.get_nodes(rule, "result") if x.text == "fail"]
            # Get all affected rules and taken their names
            for res in result:
                inplace_risk = xccdf.get_check_import_inplace_risk(rule)
                # In case that report has state fail and
                # no log_risk than it should be needs_inspection
                if not inplace_risk:
                    changed, res.text = inplace_dict[0](rule)
                else:
                    inplace_num = int(xccdf.get_and_print_inplace_risk(0, inplace_risk))
                    changed, res.text = inplace_dict[inplace_num](rule)
                if changed is not None:
                    changed_fields.append(changed+":"+res.text)

        if scanning_results:
            scanning_results.update_data(changed_fields)

        self.write_xml()

    def remove_empty_check_import(self):
        """
        This function remove check_import tag which are empty
        """
        for rule in self.get_all_result_rules():
            # Filter all check-import=stdout which are empty and remove them
            for check in self.get_nodes(rule, "check"):
                result = [x for x in self.get_nodes(check, "check-import")
                          if x.get('import-name') == "stdout" and x.text is None]
                if result:
                    for res in result:
                        remove_node(check, res)

    def remove_debug_info(self):
        """
        Function removes debug information from report
        """
        re_expr = r'^DEBUG \[\w+\]\s+.*'
        for rule in self.get_all_result_rules():
            for check_import in self.filter_grandchildren(rule,
                                                          "check",
                                                          "check-import"):
                if check_import.text is not None:
                    new_check = []
                    for check in check_import.text.split('\n'):
                        matched = re.match(re_expr, check)
                        if not matched:
                            new_check.append(check)
                    check_import.text = '\n'.join(new_check)
        self.write_xml()

    def write_xccdf_version(self, direction=False):
        """
        Function updates XCCDF version because
        of separate HTML generation and our own XSL stylesheet
        """
        namespace_1 = 'http://checklists.nist.gov/xccdf/1.1'
        namespace_2 = 'http://checklists.nist.gov/xccdf/1.2'
        content = get_file_content(self.path, "r")
        if direction:
            content = re.sub(namespace_2, namespace_1, content)
        else:
            content = re.sub(namespace_1, namespace_2, content)
        write_to_file(self.path, 'w', content)

    def update_check_description(self):
        for rule in self._get_all_rules():
            for description in self.filter_children(rule, 'description'):
                lines = description.text.split('\n')
                details = 'Details:'
                expected_results = 'Expected results:'
                attr = ' xml:lang="en"'
                tag_exp_results = expected_results[:-1].lower().replace(' ', '-')
                tag_details = details[:-1].lower()
                found = 0
                for index, line in enumerate(lines):
                    if line.strip().startswith(details):
                        found = 1
                        lines[index] = line.replace(details, '<ns0:' + tag_details + attr + '>')
                        continue
                    if line.strip().startswith(expected_results):
                        found = 1
                        lines[index] = line.replace(expected_results,
                                                    '</ns0:' + tag_details + '>\n<ns0:' + tag_exp_results + attr + '>')
                        continue
                if found == 1:
                    lines.append('</ns0:' + tag_exp_results + '>')
                    description.text = '\n'.join(lines)
        self.write_xml()

    def select_rules(self, mode):
        """
        Function marks choice a specific rules based on the content generation
        :return:
        """
        full_path = os.path.join(os.path.dirname(self.path), mode)
        try:
            lines = [i.rstrip() for i in get_file_content(full_path, 'r', method=True)]
        except IOError:
            return
        for select in self.filter_grandchildren(self.target_tree, self.profile, "select"):
            idref = select.get('idref', None)
            if idref in lines:
                select.set('selected', 'true')
            else:
                select.set('selected', 'false')
        self.write_xml()
