# -*- coding: utf-8 -*-
from __future__ import print_function
import datetime
import re
import subprocess
import fnmatch
from preup.logger import *
import shutil
from os import path, access, stat, W_OK, R_OK

def check_file(fp, mode):
    """
    Check if file exists and has set right mode
    """
    intern_mode = 0
    if(isinstance(mode,str)):
      if('w' in mode or 'a' in mode):
          intern_mode += W_OK
      if('r' in mode):
          intern_mode += R_OK
    else:
      intern_mode = mode
    if(path.exists(fp)):
        if(path.isfile(fp)):
            if(access(fp, intern_mode)):
                return True
            else:
                return False
        else:
            return False
    else:
        return False



def check_xml(xml_file):
    """
    return False if xml file is not okay or raise IOError if perms are
    not okay; use python-magic to check the file if module is available
    """
    if os.path.isfile(xml_file):
        if not os.access(xml_file, os.R_OK):
            log_message("File is not readable." % xml_file, level=logging.ERROR)
            raise IOError("File %s is not readable." % xml_file)
    else:
        log_message("%s is not a file" % xml_file, level=logging.ERROR)
        raise IOError("%s is not a file." % xml_file)
    raw_test = False
    is_valid = False
    try:
        import magic
    except ImportError:
        raw_test = True
    else:
        try:
            xml_file_magic = magic.from_file(xml_file, mime=True)
        except AttributeError:
            raw_test = True
        else:
            is_valid = xml_file_magic == 'application/xml'
    if raw_test:
        is_valid = xml_file.endswith(".xml")
    if is_valid:
        return xml_file
    else:
        log_message("Provided file is not a valid XML file", level=logging.ERROR)
        raise RuntimeError("Provided file is not a valid XML file")


def check_or_create_temp_dir(temp_dir, mode=None):
    """ check if provided temp dir is valid """
    if os.path.isdir(temp_dir):
        if not os.access(temp_dir, os.W_OK):
            log_message("Directory %s is not writable." % temp_dir, level=logging.ERROR)
            raise IOError("Directory %s is not writable." % temp_dir)
    else:
        os.makedirs(temp_dir)
    if mode:
        os.chmod(temp_dir, mode)
    return temp_dir


def get_interpreter(file, verbose=False):
    # The function returns interpreter
    # Checks extension of script and first line of script
    script_types = {'/bin/bash': '.sh',
                    '/usr/bin/python': '.py',
                    '/usr/bin/perl': '.pl'}

    inter = list(k for k, v in script_types.iteritems() if file.endswith(v))
    content = get_file_content(file, 'r')
    if inter and content.startswith('#!'+inter[0]):
        return inter
    else:
        if verbose:
            log_message("Problem with getting interpreter", level=logging.ERROR)
        return None


def print_error_msg(title="", msg="", level=' ERROR '):
    """
    Function prints a ERROR or WARNING messages
    """
    number = 10
    print ('\n')
    print ('*'*number+level+'*'*number)
    print (title, ''.join(msg))


def run_subprocess(cmd, output=None, print_output=False, shell=False, function=None):
    """ wrapper for Popen """
    sp = subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          shell=shell,
                          bufsize=1)
    stdout = ''
    for stdout_data in iter(sp.stdout.readline, b''):
        # communicate() method buffers everything in memory, we will read stdout directly
        stdout += stdout_data.decode(settings.defenc)
        if function is None:
            if print_output:
                print (stdout_data, end="", flush=True)
        else:
            function(stdout_data)
    sp.communicate()

    if output is not None:
        write_to_file(output, "wb",stdout)
    return sp.returncode


def create_dest_dir(path):
    n = datetime.datetime.now()
    stamp = n.strftime("%y%m%d%H%M%S%f")
    if path.endswith('/'):
        destdir = path[:-1] + stamp
    else:
        destdir = path + stamp
    os.makedirs(destdir)
    return destdir


def get_prefix():
    return settings.prefix


def get_system():
    """
    Check if system is Fedora or RHEL
    :return: Fedora or None
    """
    lines = get_file_content('/etc/redhat-release', 'r', method=True)
    return [line for line in lines if line.startswith('Fedora')]


def get_assessment_version(dir_name):
    if get_prefix() == "preupgrade":
        matched = re.search(r'\D+(\d*)_(\d+)', dir_name, re.I)
        if matched:
            return [matched.group(1), matched.group(2)]
        else:
            return None
    elif get_prefix() == "premigrate":
        matched = re.search(r'\D+(\d*)_\D+(\d+)', dir_name, re.I)
        if matched:
            return [matched.group(1), matched.group(2)]
        else:
            return None
    else:
        matched = re.search(r'\D+(\d*)_(\D*)(\d+)', dir_name, re.I)
        if matched:
            return [matched.group(1), matched.group(3)]
        else:
            return None


def get_valid_scenario(dir_name):
    matched = [x for x in dir_name.split(os.path.sep) if re.match(r'\D+(\d*)_(\D*)(\d+)(-results)?$', x, re.I)]
    if matched:
        return matched[0]
    else:
        return None


def get_file_content(path, perms, method=False):
    """
    shortcut for returning content of file:
     open(...).read()
     if method is False then file is read by function read
     if method is True then file is read by function readlines
    """
    try:
        f = open(path, perms)
        try:
            data = f.read().decode(settings.defenc) if not method else [line.decode(settings.defenc) for line in f.readlines()]
        finally:
            f.close()
            return data
    except IOError:
        raise


def write_to_file(path, perms, data):
    """
    shortcut for returning content of file:
     open(...).read()
    """
    try:
        f = open(path, perms)
        try:
            if isinstance(data, list):
                f.writelines([line.encode(settings.defenc) for line in data])
            else:
                f.write(data.encode(settings.defenc))
        finally:
            f.close()
    except IOError:
        raise


def get_tarball_name(result_file, time):
    return result_file.format(time)


def get_tarball_result_path(root_dir, filename):
    return os.path.join(root_dir, filename)


def get_current_time():
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")


def tarball_result_dir(result_file, dirname, quiet, direction=True):
    """
    pack results to tarball
    direction is used as a flag for packing or extracting
    For packing True
    For unpacking False
    """
    current_dir = os.getcwd()
    tar_binary = "/bin/tar"
    current_time = get_current_time()
    cmd_extract = "-xzf"
    cmd_pack = "-czvf"
    cmd = [tar_binary]
    # numeric UIDs and GIDs are used, ACLs are enabled, SELinux is enabled
    tar_options = ["--numeric-owner", "--acls", "--selinux"]

    # used for packing directories into tarball
    os.chdir(dirname)
    if direction:
        tarball = get_tarball_result_path(dirname, get_tarball_name(result_file, current_time))
        cmd.append(cmd_pack)
        cmd.append(tarball)
        cmd.append(".")
    else:
        cmd.append(cmd_extract)
        cmd.append(result_file)

    cmd.extend(tar_options)
    run_subprocess(cmd, print_output=quiet)
    if direction:
        try:
            shutil.copy(tarball, os.path.join(settings.tarball_result_dir+"/"))
        except IOError:
            log_message("Problem with copying tarball {0} to /root/preupgrade-results".format(tarball))
    os.chdir(current_dir)

    return os.path.join(settings.tarball_result_dir, get_tarball_name(result_file, current_time))


def get_upgrade_dir_path(dirname):
    """
    The function returns upgrade path dir like RHEL6_7
    If /root/preupgrade/ dir contaings RHEL6_7 dir then
    it return just RHEL6_7 dir.
    This is used for get_get_assessment_version
    """
    is_dir = lambda x: os.path.isdir(os.path.join(dirname, x))
    dirs = os.listdir(dirname)
    for d in filter(is_dir, dirs):
        upgrade_path = filter(lambda x: d in x, settings.preupgrade_dirs)
        if not upgrade_path:
            return d
    return None


def get_message(title="", message="Do you want to continue?"):
    """
    Function asks for input from user
    :param title: Title of the message
    :param message: Message text
    :return: y or n
    """
    yes = ['yes', 'y']
    yesno = yes + ['no', 'n']
    prompt = ' y/n'
    print (title)
    print (message + prompt)
    while True:
        try:
            choice = raw_input().lower()
        except KeyboardInterrupt:
            return "n"
        if choice not in yesno:
            print ('You have to choose one of y/n.')
        else:
            return choice


def get_needs_inspection():
    return settings.needs_inspection


def get_needs_action():
    return settings.needs_action


def get_convertors():
    """
    Function returns list of supported convertors
    """
    return settings.text_converters.keys()


def get_server_variant():
    """
    Function return a variant
    """
    redhat_release = get_file_content("/etc/redhat-release", "r")
    try:
        rel = redhat_release.split()
        return rel[4]
    except IndexError as ierr:
        return None


def get_addon_variant():
    """
    Function returns a addons variant if available
    83 - HighAvailability
    """
    mapping_dict = {
        '83.pem': 'HighAvailability',
        '85.pem': 'LoadBalancer',
        '90.pem': 'ResilientStorage',
        '92.pem': 'ScalableFileSystem',
    }
    variant = ['optional']
    pki_dir = "/etc/pki/product"
    if os.path.isdir(pki_dir):
        pem_files = [x for x in os.listdir(pki_dir) if x.endswith(".pem")]
        for pem in pem_files:
            # Curently we don't use the openssl command for getting certificate
            # PEM numbers are not changed between versions.
            #cmd = settings.openssl_command.format(os.path.join(pki_dir, pem))
            #lines = run_subprocess(cmd, print_output=True, shell=True)
            if pem in mapping_dict.keys():
                variant.append(mapping_dict[pem])
    return variant


def clean_directory(dir_name, pattern):
    """
    Function deleted specific files in dir_name
    :param dir_name: Dirname where the files are deleted
    :param pattern: What files with specific pattern are deleted
    :return:
    """
    for root, dirs, files in os.walk(dir_name):
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                os.unlink(os.path.join(root, f))


def remove_home_issues():
    """
    Function removes /home rows from specific files
    :return:
    """
    files = [os.path.join(settings.cache_dir, settings.common_name, 'allmyfiles.log'),
             os.path.join(settings.KS_DIR, 'untrackeduser')]
    for f in files:
        try:
            lines = get_file_content(f, 'r', method=True)
            lines = [l for l in lines if not l.startswith('/home')]
            write_to_file(f, 'w', lines)
        except IOError:
            pass


def update_platform(full_path):
    file_lines = get_file_content(full_path, 'r', method=True)
    platform = ''
    platform_id = ''
    if not get_system():
        platform = settings.CPE_RHEL
    else:
        platform = settings.CPE_FEDORA
    platform_id = get_assessment_version(full_path)
    for index, line in enumerate(file_lines):
        if 'PLATFORM_NAME' in line:
            line = line.replace('PLATFORM_NAME', platform)
        if 'PLATFORM_ID' in line:
            line = line.replace('PLATFORM_ID', platform_id[0])
        file_lines[index] = line
    write_to_file(full_path, 'w', file_lines)