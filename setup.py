#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import distutils.command.sdist
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages
from preupg.version import VERSION

project_name = "preupgrade-assistant"
project_url = "https://github.com/upgrades-migrations/preupgrade-assistant/"
project_author = "Red Hat, Inc."
project_author_email = "phracek@redhat.com"
project_description = "Preupgrade assistant"
package_name = "%s" % project_name
package_module_name = project_name
package_version = VERSION

script_files = ['bin/preupg', 'bin/premigrate', 'tools/preupg-content-creator',
                'tools/preupg-kickstart-generator', 'tools/preupg-ui-manage',
                'tools/preupg-xccdf-compose', 'tools/preupg-create-group-xml']

data_files = {
    'preupg/ui/report/fixtures/':
        ['preupg/ui/report/fixtures/initial_data.json'],
    '/usr/share/preupgrade/':
        ['common.sh', 'doc/README', 'doc/README.kickstart', 'doc/README.ui'],
    '/usr/share/doc/preupgrade-assistant/':
        ['LICENSE']
}

# Include relative path to dirs with non-python files - these will be added
# to the python module directory with the same relative path
paths = ['preupg/ui/templates/', 'preupg/ui/static/']
for path in paths:
    for root, dirs, files in os.walk(path):
        data_files[root] = [os.path.join(root, f) for f in files]

# Specify absolute paths into which content from the relative path-defined
# dirs will be copied to
paths = {'/usr/share/preupgrade/': 'data/',
         '/': 'etc/'}
for absolute_dir_base, local_relative_dir in paths.iteritems():
    for root, dirs, files in os.walk(local_relative_dir):
        absolute_dir = os.path.join(absolute_dir_base, root)
        data_files[absolute_dir] = [os.path.join(root, f) for f in files]

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
