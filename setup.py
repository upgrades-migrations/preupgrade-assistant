#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import re
import distutils.command.sdist
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages
from preupg.version import VERSION
from preupg.settings import DOC_DIR

project_name = "preupgrade-assistant"
project_url = "https://github.com/upgrades-migrations/preupgrade-assistant/"
project_author = "Red Hat, Inc."
project_author_email = "phracek@redhat.com"
project_description = "Preupgrade Assistant"
package_name = "%s" % project_name
package_module_name = project_name
package_version = VERSION

script_files = ['bin/preupg', 'tools/preupg-content-creator',
                'tools/preupg-kickstart-generator', 'tools/preupg-ui-manage',
                'tools/preupg-xccdf-compose', 'tools/preupg-create-group-xml',
                'tools/preupg-diff']

data_files = {
    'preupg/ui/report/fixtures/':
        ['preupg/ui/report/fixtures/initial_data.json'],
    '/usr/share/preupgrade/':
        ['common.sh'],
    DOC_DIR:
        ['LICENSE', 'doc/README', 'doc/README.kickstart', 'doc/README.ui']
}

# Include relative path to dirs with non-python files - these will be added
# to the python module directory with the same relative path
paths = ['preupg/ui/templates/', 'preupg/ui/static/']
for path in paths:
    for root, dirs, files in os.walk(path):
        data_files[root] = [os.path.join(root, f) for f in files]

# Specify absolute paths into which content from the relative path-defined
# dirs will be copied to
paths = {'etc/': '/etc',
         'data/': '/usr/share/preupgrade/data',
         'doc/module_writing_tutorial/':
             os.path.join(DOC_DIR, 'module_writing_tutorial')}
for relative_source_dir, absolute_dest_dir in iter(paths.items()):
    for root, dirs, files in os.walk(relative_source_dir):
        path_to_join = re.split(relative_source_dir + "/?", root)[1]
        absolute_dir = os.path.join(absolute_dest_dir, path_to_join)
        relative_file_paths = [os.path.join(root, f) for f in files]
        if relative_file_paths:
            data_files[absolute_dir] = relative_file_paths

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
