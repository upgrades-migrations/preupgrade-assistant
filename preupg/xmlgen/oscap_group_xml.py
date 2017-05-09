
"""
This class will ready the YAML file as INI file.
So no change is needed from maintainer point of view
"""

from __future__ import print_function, unicode_literals
import os
import codecs

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from preupg.xmlgen.xml_utils import XmlUtils
from preupg.utils import FileHelper, SystemIdentification
try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
from preupg import settings

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError


class OscapGroupXml(object):

    """Class creates a XML file for OpenSCAP"""

    def __init__(self, dir_name):
        self.dirname = dir_name
        if dir_name.endswith('/'):
            self.main_dir = dir_name.split('/')[-3]
        else:
            self.main_dir = dir_name.split('/')[-2]
        self.lists = []
        self.loaded = {}
        self.filename = "group.xml"
        self.rule = []
        self.ret = {}

    def find_all_ini(self):
        """
        This function is used for finding all _fix files in the user defined
        directory
        """
        for dir_name in os.listdir(self.dirname):
            if dir_name.endswith(".ini"):
                self.lists.append(os.path.join(self.dirname, dir_name))
        for file_name in self.lists:
            if FileHelper.check_file(file_name, "r") is False:
                continue
            config = configparser.ConfigParser()
            filehander = codecs.open(file_name, 'r', encoding=settings.defenc)
            config.readfp(filehander)
            fields = {}
            section = 'preupgrade'
            for option in config.options(section):
                fields[option] = config.get(section, option)
            self.loaded[file_name] = fields

    def collect_group_xmls(self):
        """The functions is used for collecting all INI files into the one."""
        # load content without decoding to unicode - ElementTree requests this
        xml_path = os.path.join(self.dirname, "group.xml")
        try:
            self.ret[self.dirname] = ElementTree.parse(xml_path).getroot()
        except ParseError as par_err:
            raise ParseError(
                "Encountered a parse error in file %s.\nDetails: %s"
                % (os.path.join(self.dirname, "group.xml"), par_err))
        return self.ret

    def write_xml(self):
        """The function is used for storing a group.xml file"""
        self.find_all_ini()
        self.write_list_rules()
        xml_utils = XmlUtils(self.dirname, self.loaded)
        self.rule = xml_utils.prepare_sections()
        file_name = os.path.join(self.dirname, "group.xml")
        try:
            FileHelper.write_to_file(file_name, "wb",
                                     ["%s" % item for item in self.rule])
        except IOError as ior:
            raise IOError('Problem with writing to file %s.\nDetails: %s'
                          % (file_name, ior.message))

    def write_profile_xml(self, target_tree):
        """The function stores all-xccdf.xml file into content directory"""
        file_name = os.path.join(self.dirname, "all-xccdf.xml")
        print ('File which can be used by Preupgrade-Assistant is: %s'
               % file_name)
        try:
            # encoding must be set! otherwise ElementTree return non-ascii
            # characters as html entities instead, which are unsusable for us
            data = ElementTree.tostring(target_tree, "utf-8")
            FileHelper.write_to_file(file_name, "wb", data, False)
        except IOError as ioe:
            raise IOError('Problem with writing to file %s.\nDetails: %s'
                          % (file_name, ioe.message))

    def write_list_rules(self):
        end_point = self.dirname.find(
            SystemIdentification.get_valid_scenario(self.dirname))
        rule_name = '_'.join(self.dirname[end_point:].split('/')[1:])
        file_list_rules = os.path.join(settings.UPGRADE_PATH,
                                       settings.file_list_rules)
        lines = []
        if os.path.exists(file_list_rules):
            lines = FileHelper.get_file_content(file_list_rules, "rb",
                                                method=True)
        else:
            lines = []
        for values in iter(self.loaded.values()):
            check_script = [v for k, v in iter(values.items())
                            if k == 'check_script']
            if check_script:
                check_script = os.path.splitext(''.join(check_script))[0]
                lines.append(settings.xccdf_tag + rule_name + '_' +
                             check_script + '\n')
        FileHelper.write_to_file(file_list_rules, "wb", lines)
