"""
This class will ready the YAML file as INI file.
So no change is needed from maintainer point of view
"""

import os
import sys
import ConfigParser
from preuputils.xml_utils import print_error_msg, XmlUtils
from preup.utils import get_file_content, write_to_file
from xml.etree import ElementTree

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError
section_preupgrade = 'preupgrade'
section_premigrate = 'premigrate'


class OscapGroupXml():
    """
    Class creates a XML file for OpenSCAP
    """
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
            with open(file_name, 'r') as stream:
                try:
                    config = ConfigParser.ConfigParser()
                    config.readfp(open(file_name))
                    fields = {}
                    if config.has_section(section_premigrate):
                        section = section_premigrate
                    else:
                        section = section_preupgrade
                    for option in config.options(section):
                        fields[option] = config.get(section, option)
                    self.loaded[file_name] = [fields]
                except ConfigParser.MissingSectionHeaderError as mshe:
                    print_error_msg(title="Missing section header")
                except ConfigParser.NoSectionError as nse:
                    print_error_msg(title="Missing section header")

    def collect_group_xmls(self):
        """
        The functions is used for collecting all YAML files into the one.
        """
        content = get_file_content(os.path.join(self.dirname, "group.xml"), "r")
        try:
            self.ret[self.dirname] = (ElementTree.fromstring(content))
        except ParseError as par_err:
            print "Encountered a parse error in file '%s', details: %s" % (self.dirname, par_err)
        return self.ret

    def write_xml(self):
        """
        The function is used for storing a group.xml file
        """
        self.find_all_ini()
        xml_utils = XmlUtils(self.dirname, self.loaded)
        self.rule = xml_utils.prepare_sections()
        file_name = os.path.join(self.dirname, "group.xml")
        try:
            write_to_file(file_name, "w", ["%s" % item for item in self.rule])
        except IOError as ior:
            print 'Problem with rite data to file %s' % file_name

    def write_profile_xml(self, target_tree):
        """
        The function stores all-xccdf.xml file into content directory
        """
        file_name = os.path.join(self.dirname, "all-xccdf.xml")
        print 'File which can be used by Preupgrade-Assistant is:\n', ''.join(file_name)
        try:
            write_to_file(file_name, "w", ElementTree.tostring(target_tree, "utf-8"))
        except IOError as ioe:
            print 'Problem with writing to file {0}'.format(file_name), ioe.message
