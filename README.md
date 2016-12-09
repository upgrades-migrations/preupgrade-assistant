# preupgrade-assistant

[![Code Health](https://landscape.io/github/phracek/preupgrade-assistant/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/preupgrade-assistant/master) [![GitLab build status](https://gitlab.com/phracek/preupgrade-assistant/badges/master/build.svg)](https://gitlab.com/phracek/preupgrade-assistant/commits/master) [![Travis CI build status](https://travis-ci.org/upgrades-migrations/preupgrade-assistant.svg?branch=master)](https://travis-ci.org/upgrades-migrations/preupgrade-assistant)

The Preupgrade Assistant performs an assessment of the system from the "upgradeability" point of view.

## Landscape scans

[**Landscape.io scans of preupgrade-assistant**](https://landscape.io/github/phracek/preupgrade-assistant/)

## Requirements for running the tool

- openscap
- openscap-engine-sce
- openscap-utils
- python-six

## Extra requirements for development and running tests

- pykickstart
- python-setuptools
- some packages you can download from this repository: [epel-release-6-8.noarch.rpm](http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm)

## How to execute the Preupgrade Assistant

Run ./preupg with root privileges, because the preupg binary needs to have an access to all files.

## Module writing tutorial

To learn how to write modules for the Preupgrade Assistant, go through
the tutorial located in the doc/module_writing_tutorial/ directory and read through
the contents of its subfolders in the numerical order (01, 02, etc.).

The tutorial will be kept up to date with the changes in the Preupgrade Assistant
and the provided API and it will probably be extended continuously to describe best practices
for writing modules.

## Contribute

See our guidelines on [how to contribute](https://github.com/upgrades-migrations/preupgrade-assistant/wiki/Contribute) to this project.

## Contact us

- On a freenode.net IRC channel #preupgrade
- Write a question as [an issue here on GitHub](https://github.com/upgrades-migrations/preupgrade-assistant/issues/new)
