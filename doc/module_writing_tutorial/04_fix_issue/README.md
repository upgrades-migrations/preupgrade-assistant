This is an example of a little bit more complex module with detail description
of the code. The module shows how to prepare a configuration file to be valid
for RHEL 7 system prior the upgrade (without modification of the original file
itself - as during the run of PA module the original system cannot be changed)
and ensure it is applied during the post-upgrade phase. Additionally shows how
to prepare post-upgrade script that will install an rpm.

The module has various possible outputs, to show how various results could be
combined in one module. So you can find inside some useful simple constructions
that are frequently used in many other already existing modules. Some parts
of this module (e.g. post-upgrade script) are presented in more simple way
in following templates.
