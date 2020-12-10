This module is applicable in the scenario when a manual action or inspection
AFTER the upgrade is needed (the report will print status `needs_inspection`).
In this case the module is executed only in case the `foo` package is installed
and signed by Red Hat (see the `applies_to` directive in the `module.ini` file.

The following list is the minimum what such module has to do:
1. Provide a text in `$SOLUTION_FILE`: a description of the problem and
   remediation instructions.
2. Use `log_medium_risk` to provide a short message that a problem was
   found (the Preupgrade Assistant requires the risk to be set to 'medium'
   in this scenario).
3. Exit by `exit_failed` to inform Preupgrade Assistant that something unusual
   happened (or the `exit $RESULT_FAILED` could be used, which does the same.
