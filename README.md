# preupgrade-assistant

[![Code Health](https://landscape.io/github/phracek/preupgrade-assistant/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/preupgrade-assistant/master) [![GitLab build status](https://gitlab.com/phracek/preupgrade-assistant/badges/master/build.svg)](https://gitlab.com/phracek/preupgrade-assistant/commits/master) [Jenkins CI build status](https://preupg.000webhostapp.com/master.svg)

Preupgrade assistant performs assessment of the system from the "upgradeability" point of view.

## Landscape scans

[**Landscape.io scans of preupgrade-assistant**](https://landscape.io/github/phracek/preupgrade-assistant/)

## Requirements for running the tool

- openscap
- openscap-engine-sce
- openscap-utils
- python-six

## Extra requirements for developement and running tests

- pykickstart
- python-setuptools
- some packages you can download from this repository: [epel-release-6-8.noarch.rpm](http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm)

## How to execute preupgrade-assistant

Just run ./preupg. But with root priviledges because of preupg binary needs to have an access to all files.

## Contribute

See our guidelines on [how to contribute](https://github.com/upgrades-migrations/preupgrade-assistant/wiki/Contribute) to this project.

## Contact us

- On a freenode.net IRC channel #preupgrade
- Write a question as [an issue here on GitHub](https://github.com/upgrades-migrations/preupgrade-assistant/issues/new)
