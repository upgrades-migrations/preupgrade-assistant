
from __future__ import unicode_literals
import os
import shutil
import six
from preup.logger import log_message, logging
try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from preup import settings
from preup.utils import get_interpreter, run_subprocess
from preup.utils import get_file_content, write_to_file


def get_all_postupgrade_files(dummy_verbose, dir_name):
    """Function gets all postupgrade files from dir_name"""
    postupg_scripts = []
    for root, dummy_sub_dirs, files in os.walk(dir_name):
        # find all files in this directory
        postupg_scripts.extend([os.path.join(root, x) for x in files])
    if not postupg_scripts:
        log_message("No postupgrade scripts available")
    return postupg_scripts


def get_hash_file(filename, hasher):
    """Function gets a hash from file"""
    content = get_file_content(filename, "rb", False, False)
    hasher.update(b'preupgrade-assistant' + content)
    return hasher.hexdigest()


def postupgrade_scripts(verbose, dirname):
    """
    The function runs postupgrade directory

    If dir does not exists the report and return
    """
    if not os.path.exists(dirname):
        log_message('There is no any %s directory' % settings.postupgrade_dir,
                    level=logging.WARNING)
        return

    postupg_scripts = get_all_postupgrade_files(verbose, dirname)
    if not postupg_scripts:
        return

    #max_length = max(list([len(x) for x in postupg_scripts]))

    log_message('Running postupgrade scripts:')
    for scr in sorted(postupg_scripts):
        interpreter = get_interpreter(scr, verbose=verbose)
        if interpreter is None:
            continue
        log_message('Executing script %s' % scr)
        cmd = "{0} {1}".format(interpreter, scr)
        run_subprocess(cmd, print_output=False, shell=True)
        log_message("Executing script %s ...done" % scr)


def get_hashes(filename):
    """Function gets all hashes from a filename"""
    if not os.path.exists(filename):
        return None
    hashed_file = get_file_content(filename, "rb").split()
    hashed_file = [x for x in hashed_file if "hashed_file" not in x]
    return hashed_file


def copy_modified_config_files(result_dir):
    """
    Function copies all modified files to dirtyconf directory.

    (files which are not mentioned in cleanconf directory)
    """
    etc_va_log = os.path.join(settings.cache_dir, settings.common_name, "rpm_etc_Va.log")
    try:
        lines = get_file_content(etc_va_log, "rb", method=True)
    except IOError:
        return
    dirty_conf = os.path.join(result_dir, settings.dirty_conf_dir)
    clean_conf = os.path.join(result_dir, settings.clean_conf_dir)
    for line in lines:
        try:
            (opts, flags, filename) = line.strip().split()
        except ValueError:
            return
        new_filename = filename[1:]
        # Check whether config file exists in cleanconf directory
        if os.path.exists(os.path.join(clean_conf, new_filename)):
            continue
        dirty_path = os.path.join(dirty_conf, os.path.dirname(new_filename))
        # Check whether dirtyconf directory with dirname(filename) exists
        if not os.path.exists(dirty_path):
            os.makedirs(dirty_path)
        # Copy filename to dirtyconf directory
        try:
            shutil.copyfile(filename, os.path.join(dirty_conf, new_filename))
        except IOError:
            continue


def hash_postupgrade_file(verbose, dirname, check=False):
    """
    The function creates hash file over all scripts in postupgrade.d directory.

    In case of remediation it checks whether checksums are different and
    print what scripts were changed.
    """
    if not os.path.exists(dirname):
        message = 'Directory {0} does not exist for creating checksum file'
        log_message(message.format(settings.postupgrade_dir), level=logging.ERROR)
        return

    postupg_scripts = get_all_postupgrade_files(verbose, dirname)
    if not postupg_scripts:
        return

    filename = settings.base_hashed_file
    if check:
        filename = settings.base_hashed_file + "_new"
    lines = []
    for post_name in postupg_scripts:
        lines.append(post_name + "=" + get_hash_file(post_name, sha1())+"\n")

    full_path_name = os.path.join(dirname, filename)
    write_to_file(full_path_name, "wb", lines)

    if check:
        hashed_file = get_hashes(os.path.join(dirname, settings.base_hashed_file))
        if hashed_file is None:
            message = 'Hashed_file is missing. Postupgrade scripts will not be executed'
            log_message(message, level=logging.WARNING)
            return False
        hashed_file_new = get_hashes(full_path_name)
        different_hashes = list(set(hashed_file).difference(set(hashed_file_new)))
        for file_name in [settings.base_hashed_file, filename]:
            os.remove(os.path.join(dirname, file_name))
        if different_hashes or len(different_hashes) > 0:
            message = 'Checksums are different in these postupgrade scripts: %s'
            log_message(message % different_hashes, level=logging.WARNING)
            return False
    return True


def special_postupgrade_scripts(result_dir):
    """
    The function copies a special postupgrade.d scripts.

    postupgrade_dict is a dictionary with old and new files
    Files are copied from
            /usr/share/preupgrade/postupgrade.d/<key> directory
    to
            /root/preupgrade/postupgrade.d/<val> directory
    with the corresponding names
    mentioned in postupgrade.d directory.
    """
    postupgrade_dict = {"copy_clean_conf.sh": "z_copy_clean_conf.sh"}

    for key, val in six.iteritems(postupgrade_dict):
        shutil.copy(os.path.join(settings.source_dir,
                                 settings.postupgrade_dir,
                                 key),
                    os.path.join(result_dir,
                                 settings.postupgrade_dir,
                                 val))
