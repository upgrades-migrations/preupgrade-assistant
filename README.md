# The Preupgrade Assistant

[![Code Health](https://landscape.io/github/phracek/preupgrade-assistant/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/preupgrade-assistant/master) ![Jenkins CI build status](https://preupg.000webhostapp.com/master.svg)

Preupgrade Assistant analyses the operating system to assess the feasibility of upgrading the system to a new major version. Such analysis includes a check for removed packages, packages replaced by partially incompatible packages, changes in libraries, users and groups, and various other services. A report of this analysis can help admins with the system upgrade by identification of potential troubles and by mitigating some of the incompatibilities. The data gathered by Preupgrade Assistant are required by [Red Hat Upgrade tool](https://github.com/upgrades-migrations/redhat-upgrade-tool) that performs an in-place upgrade of the system.

## How to build the Preupgrade Assistant package

- Create the primary packaging source: `python setup.py sdist --formats=gztar`
- The other packaging sources are in the _packaging/sources_ folder.
- Build an RPM package using specfile in the _packaging_ folder:
  ```
  rpmbuild -bs packaging/preupgrade-assistant.spec \
    --define "_sourcedir `pwd`/packaging/sources"
   ```

## How to execute the Preupgrade Assistant

- Install the preupgrade-assistant package
- The Preupgrade Assistant requires modules. Either create your own modules by following the tutorial described below or find modules for Red Hat Enterprise Linux in the [Preupgrade Assistant Modules repo](https://github.com/upgrades-migrations/preupgrade-assistant-modules).
- Run _preupg_ with root privileges.

## How to run unit tests

- Install required python modules:
  `pip install test-requirements.txt`
- Run `python setup.py test`

## Module writing tutorial

To learn how to write modules for the Preupgrade Assistant, go through the tutorial located in the _doc/module_writing_tutorial/_.

## Contribute

See our guidelines on [how to contribute](https://github.com/upgrades-migrations/preupgrade-assistant/wiki/Contribute) to this project.

## Contact us

- On a freenode.net IRC channel #preupgrade
- Write a question as [an issue here on GitHub](https://github.com/upgrades-migrations/preupgrade-assistant/issues/new)
