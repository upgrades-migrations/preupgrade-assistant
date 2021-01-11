# How to create modules for the Preupgrade Assistant
Preupgrade Assistant (PA) is framework / tool that executes PA modules. The official set of modules developed by
Red Hat handles only content provided/signed by Red Hat.
You can create your own custom PA modules to extend the
current functionality. However, the system
usually contains additional third party or custom products and applications.
You can add your custom PA modules if you want to handle migration of these products and applications automatically during the
upgrade, or if you want to automatically run additional checks to evaluate which of your
systems could be safely upgraded.

This is short tutorial how to write modules for PA.
Currently the only known use of PA is the in-place upgrade (IPU) from RHEL 6
(and derived) systems to RHEL 7, so the tutorial is focused mainly
on development of modules for the IPU. We expect that you do not want
to create your own compose (repository) with PA modules and want to
create your custom modules in the already existing compose. If you want to
create your own compose see the `00_create_own_compose/README.md` document
for more info.

[comment]: <> (Miriam: This paragraph duplicates info from the Table of Contents and isn't necessary.)
[comment]: <> (TODO: add the rest of the story to create/add a module)
[comment]: <> (TODO: do we want to keep the paragraph below?)

The text in sections below describes how to create a simple
module in the existing compose and the basic structure of the compose. If you
are interested how to write specific PA modules, see the numbered subdirectories
(except the `00_create_own_compose` directory). Each one represent a PA module
with own documentation (`README.md`) and comments in the code. Going through
these modules consecutively gives you better understanding how to write
PA modules than reading just a specific one.

#### Table of Contents
1. [The IPU RHEL 6 to RHEL 7 process](#the-ipu-rhel-6-to-rhel-7-process)
2. [Structure of the PA module](#structure-of-the-pa-module)
3. [Module templates and examples](#module-templates-and-examples)
4. [Create a new PA module](#create-a-new-pa-module)
    1. [Create a module using the preupg-content-creator utility](#create-a-module-using-the-preupg-content-creator-utility)
    2. [Create a module without using the preupg-content-creator utility](#create-a-module-without-using-the-preupg-content-creator-utility)
    3. [Structure of the compose](#structure-of-the-compose)
        1. [Compiled compose](#compiled-compose)
5. [Tips, confusing issues, ...](#tips-confusing-issues-)


## The IPU RHEL 6 to RHEL 7 process

We expect you are familiar with the IPU RHEL 6 to RHEL 7 process from the user's
POV described in the [official documentation](https://access.redhat.com/solutions/637583).

For better orientation in terminology and understanding of PA actions, here
is simplified graph of the IPU process from the technical POV. When writing modules, it's important to understand "what are" and "when are executed":
- PA modules
- pre-upgrade scripts
- post-upgrade scripts

As these are where a developer can affect the IPU process via code developed
in a PA module.

[comment]: <> (TODO: add better description once graphical version of the schema below is added)


```
   ---------------------------------------------------------------------
  | ON ORIGINAL SYSTEM                                                  |
  |       ______________________________________                        |
  |      |run PA (the preupg utility)           |                       |
  |      | → gather common data for PA modules  |                       |
  |      | → execute PA modules                 |                       |
  |      | → generate report                    |                       |
  |       --------------------------------------                        |
  |                       ↓                                             |
  |       _____________________________________                         |
  |      |user go through the generated report |                        |
  |      | → apply any changes needed prior IPU|                        |
  |      | → check suspicious stuff, ...       |                        |
  |      | → if any changes done, run PA again |                        |
  |       ------------------------------------                          |
  |                       ↓                                             |
  |---------------------------------------------------------------------|
  | (orig system, but some changes could be made now)                   |
  |       ______________________________________________                |
  |      |run RUT (the redhat-upgrade-tool utility)     |               |
  |      | → create LVM snapshots for possible rollback |               |
  |      |   (if specified on cmd)                      |               |
  |      | → calculate the upgrade (rpm) transaction    |               |
  |      | → download rpms                              |               |
  |      | → **execute pre-upgrade scripts**            |               |
  |      | → create new bootloader entry for IPU        |               |
  |       ----------------------------------------------                |
  |                      ↓                                              |
  |                   ______                                            |
  |                  |reboot|                                           |
  |                   ------                                            |
   ---------------------------------------------------------------------
                         ↓
   ---------------------------------------------------------------------
  | INSIDE THE UPGRADE ENVIRONMENT                                      |
  |       ________________________________________                      |
  |      | boot into the upgrade environment      |                     |
  |      |  → includes some actions made by RUT   |                     |
  |      |    that cannot be affected dynamically |                     |
  |       ----------------------------------------                      |
  |                      ↓                                              |
  |               ______________                                        |
  |              | upgrade rpms |                                       |
  |               --------------                                        |
  |                      ↓                                              |
  |       ________________________________________                      |
  |      | POST-UPGRADE PHASE                     |                     |
  |      |  → **execute post-upgrade scripts**    |                     |
  |      |  → cleaning...                         |                     |
  |       ----------------------------------------                      |
  |                      ↓                                              |
  |                   ______                                            |
  |                  |reboot|                                           |
  |                   ------                                            |
   ---------------------------------------------------------------------
                        ↓
               ___________________
              |selinux relabelling|
               -------------------
                        ↓
               _______________________
              |Boot to upgraded system|
               -----------------------
                        ↓
                     .......

```

## Structure of the PA module

Each PA module is standalone. No PA module should depend on another one, as there is no static order in which modules are executed. Each PA module is composed from three files:

- **module.ini** - This is "recipe" for PA and the preupg-xccdf-compose utility.
  In the "compiled" compose, the file is replaced by "module.xml" file. However
  the compilation is not necessary anymore. PA automatically compiles
  the compose in own workspace when executed.
- **check** - This is the code of the module that should be executed. Can be
  written in Bash or Python2.
- **solution.txt** - Text file used to generate the report by PA. The content
  is printed in the remediation section inside the generated report. The content can be dynamically generated
  by an actor, but the file must always exist, even if empty.

These files must always exist in each module. You can add any other files
or directories into a module as needed. To understand all possibilities of
the **module.ini** file, read this [example](https://github.com/upgrades-migrations/preupgrade-assistant/blob/master/doc/module_writing_tutorial/01_simple_informational_module/module.ini).

For example, this could be the **check** file for Bash:
```bash
#!/bin/bash

. /usr/share/preupgrade/common.sh

#END GENERATED SECTION

exit_pass
```

or for Python:
```python
#!/usr/bin/python
# -*- Mode: Python; python-indent: 8; indent-tabs-mode: t -*-

from preupg.script_api import *

#END GENERATED SECTION

exit_pass()
```

Such both examples above are equal. This example module does nothing and
only ends with the "pass" status. But you can see three important things on this
simple example:
1. Each PA module has to start with the preliminary section ended by the `#END GENERATED SECTION`
comment. Section should be always same (based on chosen language) to prevent invalid code generation
after the compose compilation (done automatically by PA).
1. That section always imports the library with PA API for modules (we suggest you to go through these libraries to see the implemented API functions; both libraries should be analogical):
    * [common.sh](https://github.com/upgrades-migrations/preupgrade-assistant/blob/master/common.sh) for Bash.
    * [script_api](https://github.com/upgrades-migrations/preupgrade-assistant/blob/master/preupg/script_api.py) for Python.
1. Every PA module have to end with a specific
exit code to report proper status to PA, otherwise it's evaluated as an error.
We suggest to use the `exit_*` functions, which refers to the correct exit codes.
See the [table](https://github.com/upgrades-migrations/preupgrade-assistant/wiki/How-modules-affect-the-Preupgrade-Assistant-return-code) for details on how the combination of exit codes and logged risks
affects the result in the generated report and PA exit codes.

## Module templates and examples

*NOTE* the perfix numbers in names of subdirectories here are for your
convenience and better orientation. They are not required in the real world.

| The module template/example | Short module description |
| -------------------------------- | --------------------------------- |
| `01_simple_informational_module` | an initial module generating just the informationa report |
| `02_inspection_needed` | the module is executed only when the `foo` package (must be signed by Red Hat!) is installed; warn user the manual inspection (or action...) **AFTER** the upgrade is needed |
| `03_action_required` | similar as the previous one, but this time, warn user the  action (including inspection) **BEFORE** the upgrade is needed |
| `04_fix_issue` | example of a more complex module, introducing a post-upgrade script. and showing how to update (prepare) a configuration file to be compatible for RHEL 7 and automatically apply it |
| `05_add_pre_upgrade_script` | Simple template showing how to add a pre-upgrade script executed by redhat-upgrade-tool (RUT) before the prompt for reboot |
| `06_add_post_upgrade_script` | Simple template showing how to add a post-upgrade script to be executed automatically during post-upgrade phase (after the RPM upgrade transaction) |
| `07_module_in_python` | Simple example of a module written in Python in case you prefer this instead of bash |
| `08_install_custom_rpms` | Template of a module installing custom rpms located in a directory |

[comment] <> (TODO: update the structure regarding suggestions from Miriam)


## Create a new PA module

We expect you want to just extend the IPU RHEL 6 -> 7 functionality. To create a new PA module from scratch, use the `preupgr-content-creator`
utility as described in the next section. To duplicate a template or an existing module and add it into the existing compose of PA modules, see the [Create a module without using the preupg-content-creator utility](#create-a-module-without-using-the-preupg-content-creator-utility) section.

### Create a module using the preupg-content-creator utility

The simplest way to create an actor is using the `preupg-content-creator`
utility:
- Go to the directory where is stored the `RHEL6_7` repository
  (if installed on RHEL 6 system, it's `/usr/share/preupgrade/`).
- Run the tool. It's interactive, so you need to enter all requested data.
  But for the module set name, enter `RHEL6_7`.

For example:
```
# preupg-content-creator
Specify the name of the module set directory in which the module will be created: RHEL6_7
The path RHEL6_7 already exists.
Do you want to create a module there? [Y/n]? y
Specify the group name which the module belongs to [system]: 3rdparty/mymodules
Specify the module name which will be created [packages]: 01_simple_informational_module
Would you like to create a BASH or Python check script? [sh/py] Bash is default. sh
Specify the module title: First informational module
Specify the module description: An example of informational module
preupg-content-creator generated these files to be updated:
- the module was created in the /usr/share/preupgrade/RHEL6_7/3rdparty/mymodules/01_simple_informational_module directory.
- the INI file which defines the module is RHEL6_7/3rdparty/mymodules/01_simple_informational_module/module.ini.
- the check script which provides an assessment is RHEL6_7/3rdparty/mymodules/01_simple_informational_module/check. Update it before you use it.
- the solution text which informs about incompatibilities RHEL6_7/3rdparty/mymodules/01_simple_informational_module/solution.txt. Update it before you use it.

To use the newly created module with the Preupgrade Assistant run these commands:
- preupg-xccdf-compose RHEL6_7
- preupg -c RHEL6_7-results/all-xccdf.xml
```

In the above example, the tool created the `01_simple_informational_module` module under
the `3rdparty/mymodules` group. The specified script language is Bash.


### Create a module without using the preupg-content-creator utility

You can also create all files of the PA module manually without the the `preupg-content-creator`
utility or copy an existing module into the compose. This is useful if you want to reorganize structure of your modules (e.g. put
them into specific groups, ...). To ensure that PA discovers your module, follow rules of the compose structure as described below. Otherwise the PA
will not process your module.

### Structure of the compose

The PA compose (alias repository of modules for PA) has a simple structure.
The top level directory of the compose
(see the [RHEL6\_7](https://github.com/upgrades-migrations/preupgrade-assistant-modules/tree/el6toel7/RHEL6_7) directory])
must contain the `properties.ini` and the `init` files. These files already exist in existing composes. If you create your own compose, make sure to add these files. 

[comment] <> (Miriam: Not sure what you're trying to say in the first sentence below)
Every directory between the top-level directory (RHEL6\_7) and a PA module
directory with, specify a group of modules. Every such group must contain the
`group.ini` file (or `group.xml`, see the following section for detail) with the `preupgrade` section and the `group_title` key and value,
specifying the name of the group:

```ini
[preupgrade]
group_title = WhateverGroupName
```

For example, refer to the group
(Databases)[https://github.com/upgrades-migrations/preupgrade-assistant-modules/tree/el6toel7/RHEL6_7/databases].
You can specify any number of groups and levels of groups (sub-groups). However,
if you create the directory structure without the `group.ini` file, any modules
under such groups will not be discovered by PA. 

Here is example of a compose with
wrong and right structure inside the top-level directory:

```
    .
    ├── databases/
      ├── mysql/
        ├── check
        ├── module.ini
        └── solution.txt
      ├── postgresql/
        ├── check
        ├── module.ini
        └── solution.txt
      └── group.ini
    ├── packages-wrong/
      └── removed-packages/
        ├── check
        ├── module.ini
        └── solution.txt
```
In the case of the `packages-wrong` directory, the `removed-packages` module is missing the `group.ini` file and
will not be discovered.


#### Compiled compose

[comment] <> (Miriam: If customers can skip this section, what's the value in including it?)

*NOTE: You do not need to worry about mixing XML and INI files in the
compose and no longer need to compile the compose. You can skip this section as it's here just to provide tech detail
about that. But you do not need to compile the compose any more.*

All above is described for the compose that is not compiled yet. In compiled
version of the compose, the mentioned INI files are replaced by XML files. In
your case, the most probably you see mixture of INI and XML files in the compose.

Nowadays, the PA compiles the compose into the XCCDF for OpenSCAP each run inside
own temporary directories, so it is not required to compile the compose via the
`preupg-xccdf-compose` manually before the run of the `preupg` command. As well,
it's possible to put "non-compiled" groups and modules into the already compiled
compose. PA will handle the compilation even in such a case. In case of the
compiled compose, the `group.ini` and `module.ini` files are transformed into
their XML (XCCDF) variants (so it's possible you find e.g. `group.xml` file
instead of `group.ini` file inside the compiled compose.

Another difference is the `all-xccdf.xml` generated file in the top-level
directory. This file is for PA the entry point into the compose and based on
this file the execution of modules is performed. Do not touch this file, is-auto
generated by PA every time. Example of compiled compose:
```
    .
    ├── databases/
      ├── mysql/
        ├── check
        ├── module.xml
        └── solution.txt
      ├── postgresql/
        ├── check
        ├── module.xml
        └── solution.txt
      └── group.xml
    └── all-xccdf.xml
```

## Tips, confusing issues, ...

1. Execution of *pre-upgrade* and *post-upgrade* scripts (do not confuse these
with PA modules execution) is in alphabetic order (path to each script is included).
So you should be able to specify your script Y will be executed after the X script.
However, in real life, it's better to not rely on it and use such 'hacks' just
in corner cases. It's always better to write your script without any dependencies
on other script results. E.g. if script X fails and script Y relies on the result
of the scripty X, the script Y could fail uncontrollably as well.

2. If your *pre-upgrade* or *post-upgrade* script was not executed, check whether
you set correctly DAC for the file (r+x). To check that, inspect `postupgrade.d`
and `preupgrade-scripts` directories under `/root/preupgrade`.

3. To ensure your *pre-upgrade* and *post-upgrade* scripts do not conflict with
another scripts (e.g. you do not replace existing script by your and vice versa),
create always directory structure corresponding with your PA modules. E.g. if you
create `RHEL6_7/3rdparty/mycustom/database/mysql` module, put your scripts under
directories respecting that structure. E.g. for post-upgrade script of such
actor: `$POSTUPGRADE_DIR/3rdparty/mycustom/database/mysql`.

4. Similar to the bullet above, to ensure there is no conflict between PA modules
(e.g. from the point of vendor of 3rd party products), vendors should put their
modules e.g. under directory representing their name.
