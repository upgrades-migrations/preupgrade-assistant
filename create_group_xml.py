#!/usr/bin/python
import os
import sys
import optparse
import re
from distutils import dir_util
from utils.generate_xml import GenerateXml
from utils.oscap_group_xml import OscapGroupXml
from utils import variables
from preup import settings, utils

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError


def main():
    parser = optparse.OptionParser(usage="%prog [options] dirname", description="Create XML files for OpenSCAP")
    parser.add_option('-g', '--group',
                      help='Generate only group.xml file.',
                      action='store_true'
                      )
    opts, args = parser.parse_args()
    if len(args) > 1:
        print 'Specify just one directory with INI file.'
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args[0]):
        print 'Dir', args[0], 'does not exists.'
        sys.exit(1)

    if args[0].endswith('/'):
        args[0] = args[0][:-1]
    # License text will not be pregenerated
    found = 0
    for d in os.listdir(args[0]):
        if d.endswith(".ini"):
            found = 1
    if not found:
        print 'In directory %s was not found any INI file.' % args[0]
        sys.exit(1)

    dir_name = utils.get_valid_scenario(args[0])
    if dir_name is None:
        print 'Dir does not contain proper scenario.'
        sys.exit(1)
    index = 0
    for i, d in enumerate(args[0].split(os.path.sep)):
        if d == dir_name:
            index = i
            break
    dir_name = '/'.join(args[0].split(os.path.sep)[:index+1])
    result_dirname = dir_name + variables.result_prefix
    dir_util.copy_tree(dir_name, result_dirname)
    dir_name = args[0].replace(dir_name, result_dirname)

    settings.autocomplete = False
    oscap_group = OscapGroupXml(dir_name)
    oscap_group.write_xml()
    ret = oscap_group.collect_group_xmls()
    generate_xml = GenerateXml(dir_name, opts.group, ret)
    target_tree = generate_xml.make_xml()
    oscap_group.write_profile_xml(target_tree)

if __name__ == "__main__":
    main()
