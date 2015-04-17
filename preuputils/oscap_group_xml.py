from __future__ import print_function

"""
This class will ready the YAML file as INI file.
So no change is needed from maintainer point of view
"""
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from preuputils.xml_utils import print_error_msg, XmlUtils
from preup.utils import get_file_content, write_to_file, check_file
from xml.etree import ElementTree
from preup import settings

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError


class OscapGroupXml(object):
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
            if(check_file(file_name, "r") is False):
                continue
            try:
                config = configparser.ConfigParser()
                config.readfp(open(file_name))
                fields = {}
                if config.has_section('premigrate'):
                    section = 'premigrate'
                else:
                    section = 'preupgrade'
                for option in config.options(section):
                    fields[option] = config.get(section, option).decode(settings.defenc)
                self.loaded[file_name] = [fields]
            except configparser.MissingSectionHeaderError as mshe:
                print_error_msg(title="Missing section header")
            except configparser.NoSectionError as nse:
                print_error_msg(title="Missing section header")

    def collect_group_xmls(self):
        """
        The functions is used for collecting all INI files into the one.
        """
        # load content withoud decoding to unicode - ElementTree requests this
        content = get_file_content(os.path.join(self.dirname, "group.xml"),
                                   "r", False, False)
        try:
            self.ret[self.dirname] = (ElementTree.parse(os.path.join(self.dirname, "group.xml")).getroot())
        except ParseError as par_err:
            print("Encountered a parse error in file ", self.dirname, " details: ", par_err)
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
            print ('Problem with rite data to file ', file_name)

    def write_profile_xml(self, target_tree):
        """
        The function stores all-xccdf.xml file into content directory
        """
        file_name = os.path.join(self.dirname, "all-xccdf.xml")
        print ('File which can be used by Preupgrade-Assistant is:\n', ''.join(file_name))
        try:
            # encoding must be set! otherwise ElementTree return non-ascii characters
            # as html entities instead, which are unsusable for us
            data = ElementTree.tostring(target_tree, "utf-8")
            write_to_file(file_name, "w", data, False)
        except IOError as ioe:
            print ('Problem with writing to file ', file_name, ioe.message)

