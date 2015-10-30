# -*- coding: utf-8 -*-


import os
import subprocess


__all__ = (
    "get_module",
    "get_git_date",
    "get_git_version",
    "write_version",
)


def get_module(path):
    """Convert path to module name."""
    result = []
    head = path
    while head != "":
        head, tail = os.path.split(head)
        result.append(tail)
    return ".".join(reversed(result))


def get_git_date(git_repo_path):
    """Return git last commit date in YYYYMMDD format."""
    cmd = "git log -n 1 --pretty=format:%ci"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("Not a git repository: %s" % git_repo_path)
    lines = proc.stdout.read().strip().split("\n")
    return lines[0].split(" ")[0].replace("-", "")


def get_git_version(git_repo_path):
    """Return git abbreviated tree hash."""
    cmd = "git log -n 1 --pretty=format:%t"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("Not a git repository: %s" % git_repo_path)
    lines = proc.stdout.read().strip().split("\n")
    return lines[0]


def write_version(file_name, version_tuple):
    fo = open(file_name, "w")
    fo.write('VERSION = (%s, %s, %s, "%s", "%s")\n' % tuple(version_tuple))
    fo.close()
