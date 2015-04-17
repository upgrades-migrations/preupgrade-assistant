# -*- coding: utf-8 -*-

import os
import re
import rpm
from preup.utils import get_file_content, write_to_file
from preup import settings


def html_escape_string(pattern):
    """
    escape single string for XML/HTML parsing
    """
    escapes = [
        ("&", "&amp;"),  # '&' has to be first!
        ("<", "&lt;"),
        (">", "&gt;"),
        ("'", "&apos;"),
        ('"', "&quot;"),
    ]
    result = pattern
    for esc, html_esc in escapes:
        result = result.replace(esc, html_esc)
    return result


def html_escape(text_list):
    """
    HTML escape text; text is a list of strings
    """
    for index, text in enumerate(text_list):
        text_list[index] = html_escape_string(text)

    return text_list


def link_update(value, extension, inplace):
    """
    Function replaces [link:sss] with either
    <a href="http:sss">sss</a> or
    <a hred="./sss">sss</a> for file link
    """
    prefix = ""
    postfix = " "
    if extension != "html":
        prefix = "html:"
        postfix = ' xmlns:html="http://www.w3.org/1999/xhtml/" '
    possible_links = ['http', 'https', 'ftp']
    if [x for x in possible_links if x in value]:
        return '<{1}a{2}href="{0}">{0}</{1}a>'.format(value.strip(),
                                                      prefix,
                                                      postfix)
    else:
        if inplace:
            return os.path.join('/root', settings.prefix, value.strip())
        if value.strip().startswith("/"):
            return ""
        else:
            return '<{1}a{2}href="./{0}">{0}</{1}a>'.format(value.strip(),
                                                            prefix,
                                                            postfix)


def bold_update(value, extension, inplace):
    """
    Function replaces [bold:sss] with <b>sss</b>
    """
    prefix = ""
    postfix = ""
    if extension != "html":
        prefix = "html:"
        postfix = ' xmlns:html="http://www.w3.org/1999/xhtml/" '
    return '<{1}b{2}>{0}</{1}b>'.format(value,
                                        prefix,
                                        postfix)


def tag_formating(text, extension):
    """
    Format tags like:
    [bold: some text] -> <b>some text</b>
    [link: http://127.0.0.1]
        ->
            <a href="http://127.0.0.1">http://127.0.0.1</a>
    [link: /var/cache/description.txt]
        ->
            <a href="/var/cache/description.txt">/var/cache/description.txt</a>
    """
    regular = r'\[(?P<tag>\w+):(?P<text>.+?)\]'
    update_dict = {
        'bold': bold_update,
        'link': link_update,
    }

    for index, line in enumerate(text):
        expr_re = re.compile(regular)
        string_match = re.findall(expr_re, line)
        if string_match:
            for match in string_match:
                # update = update_dict[string_match.group("tag")](match, extension)
                inplace = False
                if 'INPLACERISK:' in line:
                    inplace = True
                update = update_dict[match[0]](match[1], extension, inplace)
                if update != "":
                    line = re.sub(regular, update, line, count=1)
            text[index] = line
    return text


def remove_lines(string, regex_t, post_regex_t):
    """
    remove substring from string surrounded by regex
    Regexes are tuples: (regex, remove from start pos?), e.g.:
      ('<div id="main-table">', False)
    """
    s_re, remove_start = regex_t
    e_re, remove_end = post_regex_t

    s_search = re.search(s_re, string)
    e_search = re.search(e_re, string)
    if not s_search or not e_search:
        return string
    s_pos = s_search.start() if remove_start else s_search.end()
    e_pos = e_search.start() if remove_end else e_search.end()

    return string[:s_pos] + string[e_pos:]


def get_package_version(name):
    """
    Function return a package name and version
    """
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    for h in mi:
        if h['name'] == name:
            return "%s-%s-%s" % (h['name'], h['version'], h['release'])


def add_preupg_scanner_info():
    """ add info about scanner to HTML report """
    template = """          <h2>Introduction</h2>
          <div>
            <h3>Scanner</h3>
            <ul>
%s            </ul>
          </div>
"""
    line = "              <li>%s</li>\n"
    packages = [
        'preupgrade-assistant',
        'preupgrade-assistant-contents',
        'preupgrade-assistant-contents-users',
    ]
    data = ''
    for package in packages:
        nvr = get_package_version(package)
        if nvr:
            l = line % nvr
            data += l
    return template % data


def clean_html(report_path):
    """
    Function cleans a report
    """
    file_content = get_file_content(report_path, 'r')

    s_testres = ('[\t ]*<div id="intro">[\t ]*\n[\t ]*<h2>Introduction</h2>[\t ]*\n', False)
    e_testres = ('[\t ]*</table>[\t ]*\n[\t ]*</div>[\t ]*\n[\t ]*</div>[\t ]*\n', False)

    s_score = ('[\t ]*<div>[\t ]*\n[\t ]*<h3>Score</h3>\s*', True)
    e_score = ('[\t ]*</div>[\t ]*\n[\t ]*<div id="results-overview">[\t ]*\n', False)

    # remove test results
    nl = remove_lines(file_content, s_testres, e_testres)
    # remove score table
    #nl = remove_lines(nl, s_score, e_score)
    # sed XCCDF test results
    nl = re.sub('XCCDF test result', 'Preupgrade Assistant', nl)
    # add preupg nvr
    nl = re.sub('[\t ]*<h2>Introduction</h2>[\t ]*\n', add_preupg_scanner_info(), nl)

    write_to_file(report_path, 'w', nl)


class XmlManager(object):
    """
    Class operates with XML oscap result
    """
    def __init__(self, dirname, scenario, filename, result_base):
        """
        dirname contains path to result
        """
        self.dirname = dirname
        self.filename = filename.split('.')[0]
        self.result_base = result_base
        self.scenario = scenario
        self.xml_solution_files = {}

    def get_updated_text(self, solution_text, text, line, extension):
        """Function updates a text in XML file"""
        updated_text = []
        if solution_text + "_TEXT" in line.strip():
            text = tag_formating(html_escape(text), extension)
            if extension == "html":
                new_line = "<br/>\n"
            else:
                new_line = "<html:br xmlns:html='http://www.w3.org/1999/xhtml/' />\n"
            updated_text = [x.strip() + new_line for x in text]
            if updated_text:
                updated_text = line.replace(solution_text + "_TEXT",
                                            ''.join(updated_text))
            else:
                updated_text = line.replace(solution_text + "_TEXT",
                                            "").replace(solution_text + "_HTML",
                                                        "")

        else:
            updated_text = text
        return updated_text

    def _return_correct_text_file(self, section, files):
        """
        Function returns only one text file
        based on section and list of txt files from content
        directory
        """
        found = False
        file_name = None
        for key, value in self.xml_solution_files.items():
            # section is in format _<path_content>
            section_name = section[1:] + "_"
            if section_name not in key:
                continue
            found = True
            # This will return only
            try:
                file_name = [txt for txt in files if txt == value][0]
                break
            except IndexError:
                pass
        return file_name

    def update_html(self, solution_files, extension="html"):
        """
         Function updates a XML or HTML file with relevant solution
         texts
        """
        for dir_name, files in solution_files.iteritems():
            section = dir_name.replace(os.path.join(self.dirname, self.scenario),
                                       "").replace("/", "_")
            solution_text = section + "_SOLUTION_MSG"
            if extension == "html":
                solution_text = "<p>" + solution_text
            file_name = self._return_correct_text_file(section, files)
            if not file_name or file_name is None:
                continue
            text = get_file_content(os.path.join(dir_name, file_name),
                                    "r",
                                    method=True)
            orig_file = os.path.join(self.dirname,
                                     self.result_base + "." + extension)
            lines = get_file_content(orig_file, "r", method=True)

            for cnt, line in enumerate(lines):
                # If in INPLACERISK: is a [link] then update them
                # to /root/pre{migrate,upgrade}/...
                if 'INPLACERISK:' in line.strip():
                    lines[cnt] = tag_formating([line], extension)[0]
                    continue
                # Find correct block
                if solution_text not in line.strip():
                    continue
                # Get updated text if it is HTML or TEXT
                lines[cnt] = self.get_updated_text(solution_text,
                                                   text,
                                                   line,
                                                   extension)
            write_to_file(orig_file, "w", lines)

    def find_solution_files(self, xml_solution_files):
        """
        Function finds all text files in conten
        and updates XML and HTML results
        """
        solution_files = {}
        self.xml_solution_files = xml_solution_files
        for dir_name, sub_dir, file_name in os.walk(self.dirname):
            files = [x for x in file_name if x.endswith(".txt")]
            if files:
                solution_files[dir_name] = files
        self.update_html(solution_files)
        self.update_html(solution_files, extension="xml")
        clean_html(os.path.join(self.dirname, self.result_base + ".html"))

    def remove_html_information(self):
        report_path = os.path.join(self.dirname, self.result_base + ".html")
        file_content = get_file_content(report_path, 'r', method=True)
        detail_start = '<br /><br /><strong class="bold">Details:</strong><br />'
        detail_end = '[\t ]*<div class="xccdf-fixtext">'

        new_content = []
        found_section = False
        for line in file_content:
            if detail_start in line:
                found_section = True
                continue
            if detail_end in line:
                found_section = False
            if not found_section:
                new_content.append(line)

        write_to_file(report_path, 'w', new_content)
