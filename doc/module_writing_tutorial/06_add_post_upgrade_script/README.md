This is template for module creating post-upgrade script that is executed by
redhat-upgrade-tool during an early phases of the in-place upgrade (still on the
original RHEL 7 system, before the reboot).

If you want to do some checks or automatic actions when execute
redhat-upgrade-tool, before the reboot, this is what you need to do.
Basically just copy executable files into the `$POSTUPGRADE_SCRIPT_DIR`.

This templates requires:
  - rename this module when you add it into the `RHEL6_7` PA compose
  - add the post-upgrade script into this directory
  - update the `$POST_UPGRADE_SCRIPT` value regarding the name of the script
    you add
  - update the `$_POSTUPGRADE_SCRIPT_DIR` value (e.g. regarding the name the new
    name of the module
