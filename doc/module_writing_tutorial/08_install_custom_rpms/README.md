The module install all RPMs discovered inside the *postupgrade_rpms_install*
directory. The postupgrade script is located in the very same directory.
You can use this solution on your own responsibility. Be aware that
- in case the network will not be working during post-upgrade phase (depends
  on system setup), all required dependencies should be added into the directory
  as well.
- this implementation takes space 3xSizeOfDataInDirectory. So it's not good solution
  in case you want to put here many rpms. Instead of that, you can e.g. store
  all such rpms into the `/postupgrade_rpms` directory and update the postupgrade
  script to install these rpms from that dir (keep in mind, any such dir has to
  be located on rootfs!).

Requirements for use:
- rename the module
- add any rpms (with dependencies) into the `postupgrade_rpms_install` directory
- change the _POSTUPGRADE_MODULE_DIR path regarding the change name / location
  inside the PA compose to prevent unwanted overwrite from other PA modules


In case that packages cannot be installed (missing dependency, ....) an error
message is printed that packages have to be installed manually.
