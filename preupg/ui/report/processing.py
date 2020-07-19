# -*- coding: utf-8 -*-
"""
Functions for processing reports -- extracting data from XML documents
"""

from __future__ import print_function
from datetime import datetime
import logging

import re

from xml.etree import ElementTree

logger = logging.getLogger('preup_ui')


def xml_to_html(xml_str):
    """
    XML can't be easily rendered as HTML, so we need to get rid of
    namespaces, prefixes...
    """
    # get rid of all the awesome xml stuff
    # <?xml version='1.0' encoding='UTF-8'?>\n
    xml_str = re.sub('<\?xml.+\?>', '', xml_str)
    # <html:{br,p,ul,li} xmlns:html="http://www.w3.org/1999/xhtml" href=""{ /,}>
    # ditch xmlns first
    xml_str = re.sub(' xmlns:\w+?="[^"]+?"', r'', xml_str)
    # now remove tag's prefix: *:<tag>
    xml_str = re.sub('<(/?)\w*:(\w+)', r'<\1\2', xml_str)

    # fix relative link to be served by webserver
    # <a href="file:./kickstart/untrackedsystem" ...
    xml_str = re.sub(
        '<a href="(./|file:)([^"]+)"\s*>',
        r'<a href="__INSERT_URL__?path=\2" target="_blank">',
        xml_str)
    xml_str = xml_str.strip('\n')
    return xml_str


def stringify_children(node):
    if node is None or node.text is None:
        return ''
    # strip newlines added by xmlparser
    parts = [node.text.strip('\n')]

    # was node.getchildren()
    for c in node:
        # 'method' argument is not present on python-2.6:
        #   method="html"
        child_str = ElementTree.tostring(c, encoding="UTF-8")

        child_str = xml_to_html(child_str)

        parts.append(child_str)
    # filter removes possible Nones in texts and tails
    response = ''.join(filter(None, parts)).strip()
    return response


def get_nodes(tree, tag, ns='', prefix=''):
    return tree.findall(prefix + ns + tag)


def get_node(tree, tag, ns='', prefix=''):
    return tree.find(prefix + ns + tag)


def set_if_true(d, key, value):
    """ shortcut for: `if value: d[key] = value` """
    if value is not None and len(value) > 0:
        d[key] = value


class XMLReportParser(object):

    def __init__(self, report_path):
        """
        run['groups'] = [
            {
                'xccdf_id': '', 'name': '', 'rules':
                    [{'id_ref': '', 'title': '', ...}, {...}, ]
            }
        ]
        """
        self.path = report_path
        # data structure with every information
        self.run = {'groups': [], }
        # 'symlink' to rules
        self.rules = []
        # everyone loves XML
        self.element_prefix = "{http://checklists.nist.gov/xccdf/1.2}"

    def get_child(self, tree, tag):
        return get_node(tree, tag, self.element_prefix, prefix='./')

    def filter_children(self, tree, tag):
        return get_nodes(tree, tag, self.element_prefix, prefix='./')

    def has_children(self, tree, tag):
        return len(get_nodes(tree, tag, self.element_prefix, prefix='./')) > 0

    def filter_grandchildren(self, tree, parent_tag, tag):
        return tree.findall('./%s%s/%s%s' % (self.element_prefix, parent_tag, self.element_prefix, tag))

    def get_nodes_atrib(self, tree, tag, attrib):
        try:
            return self.get_child(tree, tag).attrib[attrib]
        except (KeyError, AttributeError):
            return ''

    def get_nodes_text(self, tree, tag):
        try:
            text = self.get_child(tree, tag).text
        except AttributeError:
            pass
        else:
            if text:
                return text.strip()
        return ''

    def get_test(self, key):
        """ this may throw IndexError if test is not in self.run """
        #try:
        return filter(lambda x: x['id_ref'] == key, self.rules)[0]
        #except IndexError:
        #    return ''

    def parse_rules(self, root):
        if root is None:
            return []
        rules = []
        for rule in self.filter_grandchildren(root, 'Group', 'Rule'):
            test = {}
            test['id_ref'] = rule.attrib['id']
            set_if_true(test, 'title', self.get_nodes_text(rule, 'title'))
            set_if_true(test, 'description',
                        stringify_children(self.get_child(rule, 'description')))
            set_if_true(test, 'fix', self.get_nodes_text(rule, 'fix'))
            set_if_true(test, 'fixtext', stringify_children(self.get_child(rule, 'fixtext')))
            set_if_true(test, 'fix_type',
                        self.get_nodes_atrib(rule, 'fix', 'system'))
            rules.append(test)
            self.rules.append(test)
        return rules

    def parse_groups(self, root, parent=None):
        """
        parse groups (sets of tests)

        This method is probably most tricky. It iterates over all groups recursively.
        If there is grandchild <Rule> it will extract rules.
        If there is grandchild <Group> it will recursively process it.
        """
        def has_grandchild(root_elem, parent_tag, tag):
            g = self.filter_grandchildren(root_elem, parent_tag, tag)
            return len(g) > 0

        groups = self.filter_children(root, 'Group')

        # top level groups
        for group in groups:
            if parent and not self.has_children(group, 'Group'):
                # ^this is tricky, we are facing situation where this group is not root group;
                # the problem is, that every rule has its own group so we need
                # to filter only groups which have new unprocessed tests
                continue
            group_dict = {}
            group_dict['xccdf_id'] = group.attrib['id']
            group_dict['title'] = self.get_nodes_text(group, 'title')
            set_if_true(group_dict, 'parent', parent)
            group_dict.setdefault('rules', [])

            if has_grandchild(group, 'Group', 'Rule'):
                group_dict['rules'] = self.parse_rules(group)

            self.run['groups'].append(group_dict)
            # THIS HAS TO BE AFTER ADDITION OF CURRENT GROUP (chicken-egg problem)
            if has_grandchild(group, 'Group', 'Group'):
                self.parse_groups(group, group_dict['xccdf_id'])


    def parse_test_result_logs(self, text):
        """
        parse test's logs; result is list of dicts:
        [
            {'level': '', 'date': '', 'message': ''}
        ]
        """
        if not text:
            return None, None
        text = text.strip()
        lines = text.split('\n')

        log_regex = "preupg\.log\.(?P<level>(ERROR|WARNING|INFO|DEBUG)): (?P<date_str>\S+) (?P<time>\S+) (?P<message>.+)"
        risk_regex = "preupg\.risk\.(?P<level>\w+): (?P<message>.+)"
        date_format = '%Y-%m-%d %H:%M'
        logs = []
        risks = []
        for line in lines:
            match = re.match(log_regex, line)
            if match:
                match_dict = match.groupdict()
                try:
                    dt = match_dict['date_str'] + ' ' + match_dict['time']
                except KeyError:
                    pass
                else:
                    try:
                        match_dict['date'] = datetime.strptime(dt, date_format)
                    except ValueError:
                        match_dict['date'] = None
                logs.append(match_dict)
            else:
                match = re.match(risk_regex, line)
                if match:
                    match_dict = match.groupdict()
                    risks.append(match_dict)
        return logs, risks

    def get_test_result_logs(self, elem):
        """ retrieve test's logs from xml """
        # python-2.6: find doesnt know 'name[.*]'
        # selector = 'check-import[@import-name="stderr"]'
        # text = self.get_nodes_text(elem, selector)
        if elem is None:
            return None, None
        nodes = self.filter_children(elem, 'check-import')
        found = False
        for n in nodes:
            if n.attrib.get('import-name') == 'stderr':
                found = True
                break
        if not found:
            return None, None
        text = n.text
        parsed_logs, parsed_risks = self.parse_test_result_logs(text)
        return parsed_logs, parsed_risks

    def parse_rule_results(self, root):
        """ parse info about each test result """
        # element.iter is not on python-2.6
        #for result in root.iter(self.element_prefix + 'rule-result'):
        for result in root.findall('.//' + self.element_prefix + 'rule-result'):
            result_state = self.get_nodes_text(result, 'result')
            idref = result.attrib['idref']
            if result_state in ['error', 'notchecked']:
                logger.error("Test %s crashed.", idref)
            if result_state not in ['notselected']:
                try:
                    test = self.get_test(idref)
                except IndexError:
                    logger.error("Test %s not found", idref)
                else:
                    set_if_true(test, 'result', result_state)
                    set_if_true(test, 'time', result.attrib['time'])

                    # test logs are in element check/check-import[@import-name=stdout]
                    check_elem = self.get_child(result, 'check')
                    if check_elem is not None:
                        parsed_logs, parsed_risks = self.get_test_result_logs(check_elem)
                        set_if_true(test, 'logs', parsed_logs)
                        set_if_true(test, 'risks', parsed_risks)

    def process_run_info(self, root):
        """ get information about run and info about host """
        tr = self.get_child(root, 'TestResult')
        self.run['host'] = self.get_nodes_text(tr, 'target')
        self.run['identity'] = self.get_nodes_text(tr, 'identity')
        self.run['addresses'] = []
        if tr:
            for address in get_nodes(tr, 'target-address', self.element_prefix):
                self.run['addresses'].append(address.text)
            self.run['started'] = tr.attrib['start-time']
            self.run['finished'] = tr.attrib['end-time']
            logger.debug("Started: %s, Finished: %s", self.run['started'], self.run['finished'])
        logger.debug("Host: %s, Identity: %s", self.run['host'], self.run['identity'])

    def parse_report(self):
        """ parse XML report """
        root = ElementTree.parse(self.path).getroot()
        # rules & groups first
        self.parse_groups(root)
        self.parse_rule_results(root)
        self.process_run_info(root)
        return self.run


def parse_xml_report(xml_filepath):
    r = XMLReportParser(xml_filepath)
    return r.parse_report()


def update_html_report(html_filepath):
    """Links to files and folders need to be updated to work in the Web UI."""
    with open(html_filepath, 'r') as infile:
        updated_html = re.sub(r'<a href="(./|file:)([^"]+)"\s*>',
                              r'<a href="../file/?path=\2" target="_blank">',
                              infile.read())
    with open(html_filepath, 'w') as outfile:
        outfile.write(updated_html)


def main():
    from pprint import pprint
    import sys
    try:
        r = parse_xml_report(sys.argv[1])
    except KeyError:
        print ('Usage: prog <content.xml>')
        sys.exit(1)
    pprint(r)


if __name__ == '__main__':
    main()
