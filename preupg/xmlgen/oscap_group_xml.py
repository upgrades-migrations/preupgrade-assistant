
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
from preupg.utils import FileHelper, ModuleSetUtils
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

    def __init__(self, module_set_dir, dir_name):
        """
        @param {str} module_set_dir - directory where all modules are stored
        @param {str} dir_name - directory of specific module or module-set
            directory
        """
        self.module_set_dir = module_set_dir
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
        Find all ini files in the self.dirname path. Then read each ini file
        and save all options in 'preupgrade' section with their values to
        self.loded dict:
        self.loaded[ini_file_path] = {option1: value, option2: value, ...}
        """
        for dir_name in os.listdir(self.dirname):
            if dir_name.endswith(".ini"):
                self.lists.append(os.path.join(self.dirname, dir_name))
        for file_name in self.lists:
            if FileHelper.check_file(file_name, "r") is False:
                continue
            filehander = codecs.open(file_name, 'r', encoding=settings.defenc)
            config = configparser.ConfigParser()
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
        xml_utils = XmlUtils(self.module_set_dir, self.dirname, self.loaded)
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
        print('File which can be used by Preupgrade-Assistant is: %s'
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
        module_path = self.dirname.replace(self.module_set_dir, '')
        rule_name = '_'.join(module_path.split(os.sep)[1:])
        file_list_rules = os.path.join(settings.UPGRADE_PATH,
                                       settings.file_list_rules)
        lines = []
        if os.path.exists(file_list_rules):
            lines = FileHelper.get_file_content(file_list_rules, "rb",
                                                method=True)

        # add rule only for modules (dir which contains module.ini)
        if os.path.isfile(os.path.join(self.dirname, settings.module_ini)):
            lines.append(settings.xccdf_tag + rule_name + '_check' + '\n')

        FileHelper.write_to_file(file_list_rules, "wb", lines)
