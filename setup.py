#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import distutils.command.sdist
import re
import subprocess
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages
from preup.version import VERSION

project_name            = "preupgrade-assistant"
project_url             = "https://github.com/phracek/preupgrade-assistant/"
project_author          = "Red Hat, Inc."
project_author_email    = "phracek@redhat.com"
project_description     = "Preupgrade assistant"
package_name            = "%s" % project_name
package_module_name     = project_name
package_version         = VERSION

script_files = ['preupg', 'premigrate', 'preup_ui_manage',
                'preupg-xccdf-compose', 'preupg-create-group-xml', 'preupg-content-creator']

data_files = {
    'preup_ui/report/fixtures/': ['preup_ui/report/fixtures/initial_data.json'],
    'preuputils/': ['preuputils/template.xml'],
    '/etc': ['preup-conf/preupgrade-assistant.conf'],
    '/usr/share/preupgrade/': ['common.sh', 'README', 'README.kickstart'],
    '/usr/share/preupgrade/common': ['common/scripts.txt', 'common/post_scripts.txt'],
    '/usr/share/preupgrade/kickstart': ['kickstart/default.ks', 'kickstart/finish.sh'],
    '/usr/share/preupgrade/postupgrade.d': ['postupgrade.d/copy_clean_conf.sh'],
}

# recursively add templates and static
paths = ['preup_ui/templates/', 'preup_ui/static/', 'preup_ui/lib/']
for path in paths:
    for root, dirs, files in os.walk(path):
        data_files[root] = [os.path.join(root, f) for f in files]

# override default tarball format with bzip2
distutils.command.sdist.sdist.default_format = {'posix': 'bztar'}

packages = find_packages(exclude=['tests'])

root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)

for scheme in INSTALL_SCHEMES.values():
    scheme["data"] = scheme["purelib"]

setup(
        name            = package_name,
        version         = package_version,
        url             = project_url,
        author          = project_author,
        author_email    = project_author_email,
        description     = project_description,
        packages        = packages,
        data_files      = data_files.items(),
        scripts         = script_files,
        test_suite      = 'tests.suite',
)
