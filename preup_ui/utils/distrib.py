# -*- coding: utf-8 -*-
"""
Distributive execution
"""
try:
    import paramiko
except ImportError:
    pass


def connect(address, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(address, username=username, password=password)
    return ssh


def get_content():
    return "/root/rpmbuild/BUILD/preupgrade-assistant-0.2.1/contents-users/RHEL5_6/selinux/all-xccdf.xml"


def run_remotely(address, username, password, hostrun_id):
    """
    Execute preupgrade assistant on remote host
    """
    ssh = connect(address, username, password)
    stdin, stdout, stderr = ssh.exec_command("preupg --id %d %s" % (hostrun_id, get_content()))
    for line in stderr.read().splitlines():
        print "'%s'" % line
    for line in stdout.read().splitlines():
        print "'%s'" % line


def run(address, username, password):
    """
    Execute preupgrade assistant on remote host
    """
    ssh = connect(address, username, password)
    stdin, stdout, stderr = ssh.exec_command("preupg.py %s" % get_content())
    for line in stdout.read().splitlines():
        print "'%s'" % line

def main():
    run("192.168.122.209", 'root', 'redhat')


if __name__ == '__main__':
    main()