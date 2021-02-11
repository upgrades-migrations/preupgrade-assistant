
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
from preupg.utils import FileHelper
try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
from preupg.logger import log_message, logging
from preupg import settings, exception

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
        self.filename = "group.xml"
        self.ini_path = self.get_ini_path()
        self.rule = []
        self.ret = {}

    def get_ini_path(self):
        """Find either group.ini or module.ini in the self.dirname path.
        """
        dir_content = os.listdir(self.dirname)
        preupg_inis = [settings.module_ini, settings.group_ini]
        found_preupg_inis = [ini for ini in preupg_inis if ini in dir_content]
        if len(found_preupg_inis) > 1:
            raise exception.ModuleSetFormatError(
                "Cannot prepare XCCDF for OpenSCAP",
                "group.ini and module.ini can't be both in one directory: %s"
                % self.dirname)
        elif not found_preupg_inis:
            # Check if directory contains subdirectories.
            # Report to user that group.ini file could be missing
            subdirs = [x for x in os.listdir(self.dirname)
                       if os.path.isdir(os.path.join(self.dirname, x))]
            if subdirs and 'postupgrade.d' not in self.dirname:
                log_message(
                    "group.ini file is missing in {0}".format(self.dirname),
                    level=logging.WARNING)
            return None
        else:
            return os.path.join(self.dirname, found_preupg_inis.pop())

    def get_ini_content(self, ini_path):
        """Return all key,value pairs from the 'preupgrade' section of the
        ini_path.
        """
        if FileHelper.check_file(ini_path, "r") is False:
            return {}
        filehander = codecs.open(ini_path, 'r', encoding=settings.defenc)
        config = configparser.ConfigParser()
        config.readfp(filehander)
        ini_content = {}
        section = 'preupgrade'
        for key in config.options(section):
            ini_content[key] = config.get(section, key)
        return {ini_path: ini_content}

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
        ini_content = self.get_ini_content(self.ini_path)
        self.write_list_rules()
        xml_utils = XmlUtils(self.module_set_dir, self.dirname, ini_content)
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
