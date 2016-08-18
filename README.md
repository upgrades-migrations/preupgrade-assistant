# preupgrade-assistant

[![Code Health](https://landscape.io/github/phracek/preupgrade-assistant/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/preupgrade-assistant/master) [![GitLab CI build status](https://gitlab.com/phracek/preupgrade-assistant/badges/master/build.svg)](https://gitlab.com/phracek/Preupgrade-assistant/commits/master)

Preupgrade assistant performs assessment of the system from the "upgradeability" point of view.

## Landscape scans

[**Landscape.io scans of preupgrade-assistant**](https://landscape.io/github/phracek/preupgrade-assistant/)

## Requirements

- openscap
- openscap-engine-sce
- openscap-utils
- python-six

## Extra requirements for devel and using autotests (and RHEL-6)
- some packages you can download from this repository: [epel-release-6-8.noarch.rpm](http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm)
- pykickstart
- pytest
- python-setuptools
- tito

## How to execute preupgrade-assistant

Just run ./preupg. But with root priviledges because of preupg binary needs to have an access to all files.
