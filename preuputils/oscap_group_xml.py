
"""
This class will ready the YAML file as INI file.
So no change is needed from maintainer point of view
"""

from __future__ import print_function, unicode_literals
import os
import six
import codecs

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from preuputils.xml_utils import XmlUtils
from preup.utils import MessageHelper, FileHelper, PreupgHelper
try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
from preup import settings

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

    def collect_group_xmls(self):
        """The functions is used for collecting all INI files into the one."""
        # load content without decoding to unicode - ElementTree requests this
        try:
            self.ret[self.dirname] = (ElementTree.parse(os.path.join(self.dirname, "group.xml")).getroot())
        except ParseError as par_err:
            print("Encountered a parse error in file ", self.dirname, " details: ", par_err)
        return self.ret

    def write_xml(self):
        """The function is used for storing a group.xml file"""
        self.loaded = PreupgHelper.get_all_inifiles(self.dirname)
        xml_utils = XmlUtils(self.dirname, self.loaded)
        self.rule = xml_utils.prepare_sections()
        file_name = os.path.join(self.dirname, "group.xml")
        try:
            FileHelper.write_to_file(file_name, "wb", ["%s" % item for item in self.rule])
        except IOError as ior:
            print ('Problem with write data to the file ', file_name, ior.message)

    def write_profile_xml(self, target_tree):
        """The function stores all-xccdf.xml file into content directory"""
        file_name = os.path.join(self.dirname, "all-xccdf.xml")
        print ('File which can be used by Preupgrade-Assistant is:\n', ''.join(file_name))
        try:
            # encoding must be set! otherwise ElementTree return non-ascii characters
            # as html entities instead, which are unsusable for us
            data = ElementTree.tostring(target_tree, "utf-8")
            FileHelper.write_to_file(file_name, "wb", data, False)
        except IOError as ioe:
            print ('Problem with writing to file ', file_name, ioe.message)


