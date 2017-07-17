**Tutorial on how to create a new module set for the Preupgrade Assistant:**
---

1. Create an empty _<MODULE_SET_DIR>_ directory on an arbitrary location.

2. Create new Preupgrade Assistant modules in the _<MODULE_SET_DIR>_ directory. To find out how to create a module it is recommended to follow the tutorial:
 * Go through the subdirectories within the folder with this README file in the chronological order (01_, 02_, ...)
 * The subdirectories are actually sample modules, each trying to accomplish a different task
 * The sample modules are commented to describe details about how the modules work

3. Create a _properties.ini_ file in the _<MODULE_SET_DIR>_ directory with the following content:
```
[preupgrade-assistant-modules]
srcMajorVersion=6
dstMajorVersion=7
```  
>  Note: srcMajorVersion is the major version of the current system and dstMajorVersion is the major version to which the system is to be upgraded.

4. Make sure you have installed the preupgrade-assistant-tools package, and run the _preupg-xccdf-compose_ tool as follows:

`preupg-xccdf-compose <MODULE_SET_DIR>`

5. With no problems with the module set, the tool should have prepared the module set for the use with the Preupgrade Assistant in a new _<MODULE_SET_DIR>-results_ directory

6. Run the Preupgrade Assistant with the --contents option:

`preupg -c <MODULE_SET_DIR>-results/all-xccdf.xml`
