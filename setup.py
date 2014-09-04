#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import distutils.command.sdist
from distutils.command.install import INSTALL_SCHEMES
from scripts.include import *
from setuptools import setup

project_name            = "preupgrade-assistant"
project_dirs            = ["preup", "preup_ui", "common", "preuputils"]
project_url             = "https://github.com/phracek/preupgrade-assistant/"
project_author          = "Red Hat, Inc."
project_author_email    = "phracek@redhat.com"
project_description     = "Preupgrade assistant"
package_name            = "%s" % project_name
package_module_name     = project_name
package_version         = "0.11.1"

script_files = ['preupg', 'premigrate', 'xccdf_compose', 'create_group_xml', 'preup_ui_manage']

data_files = {
    'preup_ui/report/fixtures/': ['preup_ui/report/fixtures/initial_data.json'],
    'preuputils/': ['preuputils/template.xml'],
    '/usr/share/preupgrade/': ['common.sh', 'README', 'README.kickstart'],
    '/usr/share/preupgrade/common': ['common/scripts.txt', 'common/post_scripts.txt'],
    '/usr/share/preupgrade/xsl': ['preup.xsl'],
    '/usr/share/preupgrade/postupgrade.d': ['postupgrade.d/copy_clean_conf.sh'],
    '/usr/share/premigrate/': ['common.sh', 'README', 'README.kickstart'],
    '/usr/share/premigrate/common': ['common/scripts.txt', 'common/post_scripts.txt'],
    '/usr/share/premigrate/xsl': ['preup.xsl'],
    '/usr/share/premigrate/postupgrade.d': ['postupgrade.d/copy_clean_conf.sh'],
    '/usr/share/doc/preupgrade': ['LICENSE'],
}

# recursively add templates and static
paths = ['preup_ui/templates/', 'preup_ui/static/', 'preup_ui/lib/']
for path in paths:
    for root, dirs, files in os.walk(path):
        data_files[root] = [os.path.join(root, f) for f in files]

# override default tarball format with bzip2
distutils.command.sdist.sdist.default_format = {'posix': 'bztar'}

if os.path.isdir(".git"):
    # we're building from a git repo -> store version tuple to __init__.py
    if package_version[3] == "git":
        force = True
        git_version = get_git_version(os.path.dirname(__file__))
        git_date = get_git_date(os.path.dirname(__file__))
        package_version[4] = "%s.%s" % (git_date,git_version)

packages = get_packages(project_dirs)

root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)

for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]

setup (
        name            = package_name,
        version         = package_version.replace(" ", "_").replace("-", "_"),
        url             = project_url,
        author          = project_author,
        author_email    = project_author_email,
        description     = project_description,
        packages        = packages,
        data_files      = data_files.items(),
        scripts         = script_files,
        test_suite      = 'tests.suite',
)
