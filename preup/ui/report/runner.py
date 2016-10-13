# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

import os
import logging

from utils.scan import run_subprocess
from utils.distrib import run_remotely


logger = logging.getLogger('preup_ui')


class DummyConf(object):
    pass


def get_local_conf():
    c = DummyConf()
    c.skip_common = False
    c.quiet = False
    #c.profile = "xccdf_org.preupgrade-content_profile_fedora-default"
    c.list = None
    c.scan = 'RHEL6_7'
    c.force = True
    return c


def build_command():
    """ Build command which triggers analysis """


def run_locally(request):
    """
    DEPRECATED: do not use!
    suid binary is not being compiled atm because it's insecure

    Run analysis locally
    """
    #command = ["preupg_runner", "--force", "--upload"]
    command.append(
        request.build_absolute_uri(reverse('xmlrpc-submit'))
    )
    logger.info("Starting scan.")
    rvalue = run_subprocess(command, log=False)
    if rvalue != 0:
        logger.error("Scan failed.")
        raise RuntimeError("""\
Scan wasn't successful. If you have SELinux enabled, \
please make sure that SELinux boolean 'httpd_run_preupgrade' is enabled.""")


def run(request):
    """
    Entry point. Run scan distributively on provided set of hosts
    """
    #if run_object.has_local():
    run_locally(request)
    #for remote in run_object.remotes():
    #    print 'running on remote', remote
    #    run_remotely(remote.host.hostname, remote.host.ssh_name, remote.host.ssh_password, remote.id)


def main():
    pass

if __name__ == '__main__':
    main()
