# -*- coding: utf-8 -*-

"""
Valid settings are:

# dir where results of analysis are stored
result_dir = "/var/tmp/preupgrade"

# xccdf profile
profile = "xccdf_preupg_profile_default"

# URL of frontend
frontend = ""

# name of dir with common files
common_name = "common"

# absolute path to dir with common files
common_dir = os.path.join(os.path.dirname(__file__),"..", common_name)

# path to file with definitions of common scripts
common_script = os.path.join(common_dir, "scripts.txt")

# name of file for results
results = 'results'

# print more data into stdout
verbose = 1

# skip generation of common files
skip_common = False

# SCE XML file
sce_xml = 'sce.xml'

# enable debugging
debug = False

# id of run in frontend
id = 123456

# prefix of tag in fccdf files
xccdf_tag = "xccdf_preupg_rule_"
"""

from __future__ import unicode_literals

class DummyConf(object):
    """
    Dummy conf class for Conf

    use it like this:
    conf = Conf(DummyConf(id=123, skip_common=True))
    """
    def __init__(self, **kwargs):
        self.settings = kwargs

    def __getattr__(self, name):
        try:
            return self.settings.get(name)
        except AttributeError:
            return object.__getattribute__(self, name)


class Conf(object):
    """
    configuration of preupgrade assistant

    merged values from CLI and settings.py
    """

    def __init__(self, *args):
        """
        *args - list of objects with settings attached as
                attributes to these objects
        priority:
            args[0] > args[1] > ...
        """
        self.settings = list(args)

    def insert(self, pos, settings):
        self.settings.insert(pos, settings)

    def __getattr__(self, name):
        for arg in self.settings:
            try:
                value = getattr(arg, name)
            except AttributeError:
                continue
            if value is not None and value != "":
                return value
            else:
                continue
        #return object.__getattribute__(self, name)
        return None
