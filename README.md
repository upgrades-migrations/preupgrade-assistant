# The Preupgrade Assistant

[![Code Health](https://landscape.io/github/phracek/preupgrade-assistant/master/landscape.svg?style=flat)](https://landscape.io/github/phracek/preupgrade-assistant/master) ![Jenkins CI build status](https://preupg.000webhostapp.com/master.svg)

The Preupgrade Assistant is a diagnostics utility that assesses the system for possible in-place upgrade limitations and provides a report with the analysis results. It is based on a module system, with each module performing a separate test, checking for package removals, incompatible obsoletes, changes in libraries, name changes, or deficiencies in the compatibilities of certain configuration files. The data gathered by the Preupgrade Assistant can be used for cloning the system. It also provides post-upgrade scripts to finish more complex problems after the in-place upgrade. The Preupgrade Assistant utility is a prerequisite for completing a successful in-place upgrade to the next major version of Red Hat Enterprise Linux. The data gathered by the Preupgrade Assistant is required by [Red Hat Upgrade Tool](https://github.com/upgrades-migrations/redhat-upgrade-tool), which performs the in-place upgrade of the system.

## Building a Preupgrade Assistant package

- Create the primary packaging source by entering: `python setup.py sdist --formats=gztar`. Note: The other packaging sources are in the `packaging/sources/` folder.
- Build an RPM package by using a specfile in the `packaging/` folder:
  ```
  rpmbuild -bs packaging/preupgrade-assistant.spec \
    --define "_sourcedir `pwd`/packaging/sources"
   ```

## Executing the Preupgrade Assistant

- Install the _preupgrade-assistant_ package.
- The Preupgrade Assistant requires modules. Either create your own modules by following the tutorial described below, or find modules for Red Hat Enterprise Linux in the [Preupgrade Assistant Modules repository](https://github.com/upgrades-migrations/preupgrade-assistant-modules).
- Run the `preupg` command with root privileges.

## Running unit tests

- To install required python modules, enter:
  `pip install test-requirements.txt`
- Enter the `python setup.py test` command.

## Learning how to write modules

To learn how to write modules for the Preupgrade Assistant, see the tutorial located in the `doc/module_writing_tutorial` file.

## Contributing

See our guidelines on [how to contribute to this project](https://github.com/upgrades-migrations/preupgrade-assistant/wiki/Contribute).

### Contact us on the freenode.net IRC channel #preupgrade, or write a question as [an issue on GitHub](https://github.com/upgrades-migrations/preupgrade-assistant/issues/new).

