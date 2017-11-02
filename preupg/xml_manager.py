# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import os
import re
try:
    import rpm
except ImportError:
    pass
from preupg.utils import FileHelper
from preupg import settings
from preupg.logger import logger_report


def html_escape(text):
    """
    HTML escape text; text is a list of strings
    """
    escapes = [
        ("&", "&amp;"),  # '&' has to be first!
        ("<", "&lt;"),
        (">", "&gt;"),
        ("'", "&apos;"),
        ('"', "&quot;"),
    ]
    for esc, html_esc in escapes:
        text = text.replace(esc, html_esc)
    return text


def link_update(value):
    """
    Function replaces [link:sss] with either
    <a href="http:sss">sss</a> or
    <a href="./sss">sss</a> for file link
    """
    possible_links = ['http', 'https', 'ftp']
    if [x for x in possible_links if x in value]:
        return '<a href="{0}">{0}</a>'.format(value.strip())
    else:
        if value.strip().startswith("/") or value.strip().startswith(".."):
            return value.strip()
        else:
            return '<a href="./{0}">{0}</a>'.format(value.strip())


def bold_update(value):
    """
    Function replaces [bold:sss] with <b>sss</b>
    """
    return '<b>{0}</b>'.format(value)


def tag_formating(text):
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
    def repl(match):
        if match.group("tag") == 'bold':
            return bold_update(match.group("text"))
        elif match.group("tag") == 'link':
            return link_update(match.group("text"))
        else:
            return match.group(0)  # return the original matched string

    regular = re.compile(r'\[(?P<tag>\w+):(?P<text>.+?)\]', re.MULTILINE)
    return re.sub(regular, repl, text)


def get_package_version(name):
    """
    Function return a package name and version
    """
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    for h in mi:
        if h['name'] == name:
            return "%s-%s-%s" % (h['name'], h['version'], h['release'])


class XmlManager(object):
    """
    Class operates with XML oscap result
    """
    def __init__(self, assessment_result_path, copied_module_set_path):
        """
        assessment_result_path .. path to the directory where all results of
                                  the assessment are stored
        copied_module_set_path .. path to the module set directory copied for
                                 the assessment to the assessment_result_path
        """
        self.assessment_result_path = assessment_result_path
        self.copied_module_set_path = copied_module_set_path
        self.paths_to_all_modules = self.get_module_dirs()
        self.solution_texts = {}

    def update_report(self, report_path):
        """Update XML or HTML report with relevant solution texts."""
        if not self.solution_texts:
            self.load_solution_texts()

        orig_file = os.path.join(self.assessment_result_path, report_path)
        report_content = FileHelper.get_file_content(orig_file, "rb")

        for solution_placeholer, solution_text in self.solution_texts.items():
            report_content = report_content.replace(solution_placeholer,
                                                    solution_text)

        FileHelper.write_to_file(orig_file, "wb", report_content)

    def load_solution_texts(self):
        """Load solution texts into a dictionary."""
        for dir_name in self.paths_to_all_modules:
            section = dir_name.replace(
                self.copied_module_set_path, "").replace("/", "_")
            solution_placeholder = section + "_SOLUTION_MSG"

            logger_report.debug("Processing solution placeholder '%s'",
                                solution_placeholder)
            try:
                solution_text = FileHelper.get_file_content(
                    os.path.join(dir_name, settings.solution_txt), "rb")
            except IOError:
                # solution file is not mandatory
                solution_text = ""

            updated_solution_text = self.get_updated_solution(solution_text)
            self.solution_texts[solution_placeholder] = updated_solution_text

    def get_updated_solution(self, solution_text):
        """Function converts the solution text to HTML"""
        formatted_text = tag_formating(html_escape(solution_text))
        formatted_text = formatted_text.replace("\n", "<br/>\n")
        return formatted_text

    def get_module_dirs(self):
        """Find all directories that contain a module."""
        paths_to_all_modules = []
        for path, _, dir_files in os.walk(self.assessment_result_path):
            # Each module has its INI file
            if settings.check_script in dir_files:
                paths_to_all_modules.append(path)
        return paths_to_all_modules
