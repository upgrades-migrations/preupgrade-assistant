#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import distutils.command.sdist
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages
from preup.version import VERSION

project_name = "preupgrade-assistant"
project_url = "https://github.com/upgrades-migrations/preupgrade-assistant/"
project_author = "Red Hat, Inc."
project_author_email = "phracek@redhat.com"
project_description = "Preupgrade assistant"
package_name = "%s" % project_name
package_module_name = project_name
package_version = VERSION

script_files = ['preupg', 'premigrate', 'tools/preupg-kickstart-generator',
                'tools/preupg-xccdf-compose', 'tools/preupg-create-group-xml',
                'tools/preupg-content-creator', 'tools/preup_ui_manage']

data_files = {
    'preup/ui/report/fixtures/':
        ['preup/ui/report/fixtures/initial_data.json'],
    'preup/xml/':
        ['preup/xml/xccdf_template.xml'],
    '/etc':
        ['etc/preupgrade-assistant.conf'],
    '/usr/share/preupgrade/':
        ['common.sh', 'doc/README', 'doc/README.kickstart', 'doc/README.ui'],
    '/usr/share/preupgrade/common':
        ['data/preassesment/scripts.txt'],
    '/usr/share/preupgrade/kickstart':
        ['data/templates/migration.ks', 'data/templates/post_migration.sh'],
    '/usr/share/preupgrade/postupgrade.d':
        ['data/postupgrade.d/copy_clean_conf.sh']
}

paths = ['preup/ui/templates/', 'preup/ui/static/']
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
    name=package_name,
    version=package_version,
    url=project_url,
    author=project_author,
    author_email=project_author_email,
    description=project_description,
    packages=packages,
    data_files=data_files.items(),
    scripts=script_files,
    test_suite='tests.suite'
)
