# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import six
import datetime
import re
import subprocess
import fnmatch
import os
import sys
import shutil
import ConfigParser
import mimetypes
import platform

from preup import settings
from preup.logger import log_message, logging

from os import path, access, W_OK, R_OK, X_OK

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1


def get_current_time():
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")


class MessageHelper(object):

    @staticmethod
    def print_error_msg(title="", msg="", level=' ERROR '):
        """Function prints a ERROR or WARNING messages"""
        number = 10
        print('\n')
        print('*' * number + level + '*' * number)
        print(title, ''.join(msg))

    @staticmethod
    def get_message(title="", message="Do you want to continue?", prompt=None):
        """
        Function asks for input from user

        :param title: Title of the message
        :param message: Message text
        :return: y or n
        """
        yes = ['yes', 'y', 'Y', 'Yes']
        yesno = yes + ['no', 'n', 'N', 'No']
        print (title)
        if prompt is not None:
            print (message + prompt)
        else:
            print (message)
        while True:
            try:
                if int(sys.version_info[0]) == 2:
                    choice = raw_input()
                else:
                    choice = input()
            except KeyboardInterrupt:
                raise
            if prompt and choice not in yesno:
                print ('You have to choose one of y/n.')
            else:
                return choice


class FileHelper(object):

    @staticmethod
    def check_file(fp, mode):
        """
        Check if file exists and has set right mode

        mode can be in string format as for function open (available letters: wrax)
        or int number (in that case prefered are os constants W_OK, R_OK, X_OK)
        (letter 'a' has same signification as 'w', is here due to compatibility
        with open mode)
        """
        intern_mode = 0
        if isinstance(mode, six.text_type):
            if 'w' in mode or 'a' in mode:
                intern_mode += W_OK
            if 'r' in mode:
                intern_mode += R_OK
            if 'x' in mode:
                intern_mode += X_OK
        else:
            intern_mode = mode
        if path.exists(fp):
            if path.isfile(fp):
                if access(fp, intern_mode):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    @staticmethod
    def check_xml(xml_file):
        """
        Check XML

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

    @staticmethod
    def get_interpreter(filename, verbose=False):
        """
        The function returns interpreter

        Checks extension of script and first line of script
        """
        script_types = {'/bin/bash': '.sh',
                        '/usr/bin/python': '.py',
                        '/usr/bin/perl': '.pl'}
        inter = list(k for k, v in six.iteritems(script_types) if filename.endswith(v))
        content = FileHelper.get_file_content(filename, 'rb')
        if inter and content.startswith('#!'+inter[0]):
            return inter
        else:
            if verbose:
                log_message("Problem with getting interpreter", level=logging.ERROR)
            return None

    @staticmethod
    def get_file_content(path, perms, method=False, decode_flag=True):
        """
        shortcut for returning content of file

        open(...).read()...
        if method is False then file is read by function read
        if method is True then file is read by function readlines
        When decode_flag is True, read string is decoded to unicode. Otherwise
        only read. (Some libraries request non-unicode strings - as ElementTree)
        """

        # data must be init due to possible troubles with binary data
        data = None
        try:
            f = open(path, perms)
            try:
                if decode_flag is True:
                    data = f.read().decode(settings.defenc) if not method else [line.decode(settings.defenc) for line in f.readlines()]
                else:
                    data = f.read() if not method else f.readlines()
            finally:
                f.close()
        except IOError:
            raise
        if data is None:
            raise ValueError("You try decode binary data to unicode: %s" % path)
        return data

    @staticmethod
    def write_to_file(path, perms, data, encode_flag=True):
        """
        shortcut for write of data to file:

        open(...).write()...
        data can be string or list of strings

        data contains unicode string(s) in most cases, so we encode them
        to system default encoding before write. When you use encoded strings,
        set encode_flag to False to suppress second encodiding process.
        """
        try:
            f = open(path, perms)
            try:
                if isinstance(data, list):
                    if encode_flag is True:
                        data = [line.encode(settings.defenc) for line in data]
                    f.writelines(data)
                else:
                    # TODO: May we should print warn w
                    if encode_flag is True and isinstance(data, six.text_type):
                        f.write(data.encode(settings.defenc))
                    else:
                        f.write(data)
            finally:
                f.close()
        except IOError:
            raise

    @staticmethod
    def remove_home_issues():
        """
        Function removes /home rows from specific files

        :return:
        """
        files = [os.path.join(settings.cache_dir, settings.common_name, 'allmyfiles.log'),
                 os.path.join(settings.KS_DIR, 'untrackeduser')]
        for f in files:
            try:
                lines = FileHelper.get_file_content(f, 'rb', method=True)
                lines = [l for l in lines if not l.startswith('/home')]
                FileHelper.write_to_file(f, 'wb', lines)
            except IOError:
                pass

    @staticmethod
    def check_executable(file_name):
        """
        The function checks whether script is executable.
        If not then ERROR message arise
        """
        if not os.access(file_name, os.X_OK):
            MessageHelper.print_error_msg(title="The file %s is not executable" % file_name)

    @staticmethod
    def get_script_type(file_name):
        """
        The function returns type of check_script.
        If it's not any script then return just txt
        """
        mime_type = mimetypes.guess_type(file_name)[0]
        if mime_type is None:
            # try get mime type with shebang
            line = FileHelper.get_file_content(file_name, "rb", True)[0]
            if line.startswith("#!"):
                if re.search(r"\bpython[0-9.-]*\b", line):
                    return 'python'
                if re.search(r"\bperl[0-9.-]*\b", line):
                    return 'perl'
                if re.search(r"\bcsh\b", line):
                    return 'csh'
                if re.search(r"\b(bash|sh)\b", line):
                    return 'sh'
        file_types = {'text/x-python': 'python',
                      'application/x-csh': 'csh',
                      'application/x-sh': 'sh',
                      'application/x-perl': 'perl',
                      'text/plain': 'txt',
                      None: 'txt',
                      }
        return file_types[mime_type]


class DirHelper(object):

    @staticmethod
    def check_or_create_temp_dir(temp_dir, mode=None):
        """Check if provided temp dir is valid."""
        if os.path.isdir(temp_dir):
            if not os.access(temp_dir, os.W_OK):
                log_message("Directory %s is not writable." % temp_dir, level=logging.ERROR)
                raise IOError("Directory %s is not writable." % temp_dir)
        else:
            os.makedirs(temp_dir)
        if mode:
            os.chmod(temp_dir, mode)
        return temp_dir

    @staticmethod
    def create_dest_dir(path):
        n = datetime.datetime.now()
        stamp = n.strftime("%y%m%d%H%M%S%f")
        if path.endswith('/'):
            destdir = path[:-1] + stamp
        else:
            destdir = path + stamp
        os.makedirs(destdir)
        return destdir

    @staticmethod
    def clean_directory(dir_name, pattern):
        """
        Function deleted specific files in dir_name

        :param dir_name: Dirname where the files are deleted
        :param pattern: What files with specific pattern are deleted
        :return:
        """
        for root, dummy_dirs, files in os.walk(dir_name):
            for f in files:
                if fnmatch.fnmatch(f, pattern):
                    os.unlink(os.path.join(root, f))

    @staticmethod
    def get_upgrade_dir_path(dirname):
        """
        The function returns upgrade path dir like RHEL6_7

        If /root/preupgrade/ dir contaings RHEL6_7 dir then
        it return just RHEL6_7 dir.
        This is used for get_assessment_version
        """
        is_dir = lambda x: os.path.isdir(os.path.join(dirname, x))
        dirs = os.listdir(dirname)
        for d in filter(is_dir, dirs):
            upgrade_path = filter(lambda x: d in x, settings.preupgrade_dirs)
            if not upgrade_path:
                return d
        return None


class ProcessHelper(object):

    @staticmethod
    def run_subprocess(cmd, output=None, print_output=False, shell=False, function=None):
        """wrapper for Popen"""
        sp = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              shell=shell,
                              bufsize=1)
        stdout = six.binary_type() # FIXME should't be this bytes()?
        for stdout_data in iter(sp.stdout.readline, b''):
            # communicate() method buffers everything in memory, we will read stdout directly
            stdout += stdout_data
            if function is None:
                if print_output:
                    print (stdout_data, end="")
                else:
                    pass
            else:
                # I don't know what functions can come here, however
                # it's not common so put only unicode data here again.
                # Should be always raw data so we don't need test stdout_data
                # on type
                function(stdout_data.decode(settings.defenc))
        sp.communicate()

        if output is not None:
            # raw data, so without encoding
            FileHelper.write_to_file(output, "wb", stdout, False)
        return sp.returncode


class PreupgHelper(object):
    @staticmethod
    def get_prefix():
        return settings.prefix


class SystemIdentification(object):

    @staticmethod
    def get_system():
        """
        Check if system is Fedora or RHEL

        :return: Fedora or None
        """
        lines = FileHelper.get_file_content('/etc/redhat-release', 'rb', method=True)
        return [line for line in lines if line.startswith('Fedora')]

    @staticmethod
    def get_arch():
        return platform.machine()

    @staticmethod
    def get_convertors():
        """Function returns list of supported convertors"""
        return settings.text_converters.keys()

    @staticmethod
    def get_assessment_version(dir_name):
        if PreupgHelper.get_prefix() == "preupgrade":
            matched = re.search(r'\D+(\d*)_(\d+)', dir_name, re.I)
            if matched:
                return [matched.group(1), matched.group(2)]
            else:
                return None
        elif PreupgHelper.get_prefix() == "premigrate":
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

    @staticmethod
    def get_valid_scenario(dir_name):
        matched = [x for x in dir_name.split(os.path.sep) if re.match(r'\D+(\d*)_(\D*)(\d+)(-results)?$', x, re.I)]
        if matched:
            return matched[0]
        else:
            return None

    @staticmethod
    def get_variant():
        """Function return a variant"""
        redhat_release = FileHelper.get_file_content("/etc/redhat-release", "rb")
        if redhat_release.startswith('Fedora'):
            return None
        try:
            rel = redhat_release.split()
            return rel[4]
        except IndexError:
            return None

    @staticmethod
    def get_addon_variant():
        """
        Function returns a addons variant if available

        83 - HighAvailability
        85 - LoadBalancer
        90 - ResilientStorage
        92 - ScalableFileSystem
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


class TarballHelper(object):

    @staticmethod
    def get_tarball_name(result_file, time):
        return result_file.format(time)

    @staticmethod
    def get_tarball_result_path(root_dir, filename):
        return os.path.join(root_dir, filename)

    @staticmethod
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
        os.chdir('/root')
        tarball_dir = TarballHelper.get_tarball_name(result_file, current_time)
        tarball_name = tarball_dir + '.tar.gz'
        bkp_tar_dir = os.path.join('/root', tarball_dir)
        if direction:
            if not os.path.exists(bkp_tar_dir):
                os.makedirs(bkp_tar_dir)
            for preupg_dir in settings.preupgrade_dirs:
                shutil.copytree(os.path.join(dirname, preupg_dir),
                                os.path.join(bkp_tar_dir, preupg_dir),
                                symlinks=True)
            tarball = TarballHelper.get_tarball_result_path(dirname, tarball_name)
            cmd.append(cmd_pack)
            cmd.append(tarball)
            cmd.append(tarball_dir)
        else:
            cmd.append(cmd_extract)
            cmd.append(result_file)

        cmd.extend(tar_options)
        ProcessHelper.run_subprocess(cmd, print_output=quiet)
        shutil.rmtree(bkp_tar_dir)
        if direction:
            try:
                shutil.copy(tarball, os.path.join(settings.tarball_result_dir+"/"))
            except IOError:
                log_message("Problem with copying tarball {0} to /root/preupgrade-results".format(tarball))
        os.chdir(current_dir)

        return os.path.join(settings.tarball_result_dir, tarball_name)

    @staticmethod
    def get_default_tarball_path(result_dir, tarball_name):
        """Returns full tarball path"""
        return os.path.join(result_dir, tarball_name)


class ConfigHelper(object):
    @staticmethod
    def get_preupg_config_file(path, key, section="preupgrade"):
        if not os.path.exists(path):
            return None

        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.read(path)
        section = 'preupgrade-assistant'
        if config.has_section(section):
            if config.has_option(section, key):
                return config.get(section, key)


class ConfigFilesHelper(object):
    @staticmethod
    def check_cleanconf_dir(result_dir, cleanconf):
        # Check if configuration file exists in /root/preupgrade/cleanconf directory
        clean_conf_name = os.path.join(result_dir, cleanconf)
        if os.path.exists(clean_conf_name):
            message = "Configuration file '%s' exists in '%s' directory"
            log_message(message % (clean_conf_name, os.path.dirname(clean_conf_name)),
                        print_output=0,
                        level=logging.INFO)
            # Check if configuration file exists in dirtyconf
            # If so delete them.
            return True
        return False

    @staticmethod
    def check_dirtyconf_dir(dirtyconf, filename):
        # Check if configuration file exists in /root/preupgrade/dirtyconf directory
        # If not return real path of configuration file. Not a symlink.
        dirty_path = os.path.join(os.path.dirname(dirtyconf), filename)
        full_path = filename
        # Copy filename to dirtyconf directory
        # Check if file is a symlink or real path.
        if os.path.islink(full_path):
            full_path = os.path.realpath(full_path)
        # Check if configuration file exists in dirtyconf directory
        if os.path.exists(dirtyconf):
            log_message("File '%s' already exists in dirtyconf directory" % dirtyconf,
                        print_output=0,
                        level=logging.INFO)
            return False
        # Check whether dirtyconf directory with dirname(filename) exists
        if not os.path.exists(os.path.dirname(dirtyconf)):
            os.makedirs(os.path.dirname(dirtyconf))
        return full_path

    @staticmethod
    def copy_modified_config_files(result_dir):
        """
        Function copies all modified files to dirtyconf directory.

        (files which are not mentioned in cleanconf directory)
        """
        etc_va_log = os.path.join(settings.cache_dir, settings.common_name, "rpm_etc_Va.log")
        try:
            lines = FileHelper.get_file_content(etc_va_log, "rb", method=True)
        except IOError:
            return
        dirty_conf = os.path.join(result_dir, settings.dirty_conf_dir)
        clean_conf = os.path.join(result_dir, settings.clean_conf_dir)
        # Go through all changed config files
        for line in lines:
            try:
                (opts, flags, filename) = line.strip().split()
            except ValueError:
                return
            log_message("File name to copy '%s'" % filename,
                        print_output=0,
                        level=logging.INFO)
            new_filename = filename[1:]
            # Check whether config file exists in cleanconf directory
            cleanconf_file_name = os.path.join(clean_conf, new_filename)
            dirtyconf_file_name = os.path.join(dirty_conf, new_filename)
            # Check if config file does not exist in cleanconf directory
            if ConfigFilesHelper.check_cleanconf_dir(result_dir, cleanconf_file_name):
                if os.path.exists(dirtyconf_file_name):
                    log_message("File %s exist in %s directory" % (new_filename, dirty_conf), logging.DEBUG)
                    os.unlink(dirtyconf_file_name)
                continue
            # Check if config file does not exists in dirtyconf directory
            check = ConfigFilesHelper.check_dirtyconf_dir(dirtyconf_file_name, filename)
            if check:
                shutil.copyfile(check, dirtyconf_file_name)


class PostupgradeHelper(object):

    @staticmethod
    def get_all_postupgrade_files(dummy_verbose, dir_name):
        """Function gets all postupgrade files from dir_name"""
        postupg_scripts = []
        for root, dummy_sub_dirs, files in os.walk(dir_name):
            # find all files in this directory
            postupg_scripts.extend([os.path.join(root, x) for x in files])
        if not postupg_scripts:
            log_message("No postupgrade scripts available")
        return postupg_scripts

    @staticmethod
    def get_hash_file(filename, hasher):
        """Function gets a hash from file"""
        content = FileHelper.get_file_content(filename, "rb", False, False)
        hasher.update(b'preupgrade-assistant' + content)
        return hasher.hexdigest()


    @staticmethod
    def postupgrade_scripts(verbose, dirname):
        """
        The function runs postupgrade directory

        If dir does not exists the report and return
        """
        if not os.path.exists(dirname):
            log_message('There is no any %s directory' % settings.postupgrade_dir,
                        level=logging.WARNING)
            return

        postupg_scripts = PostupgradeHelper.get_all_postupgrade_files(verbose, dirname)
        if not postupg_scripts:
            return

        #max_length = max(list([len(x) for x in postupg_scripts]))

        log_message('Running postupgrade scripts:')
        for scr in sorted(postupg_scripts):
            interpreter = FileHelper.get_interpreter(scr, verbose=verbose)
            if interpreter is None:
                continue
            log_message('Executing script %s' % scr)
            cmd = "{0} {1}".format(interpreter, scr)
            ProcessHelper.run_subprocess(cmd, print_output=False, shell=True)
            log_message("Executing script %s ...done" % scr)

    @staticmethod
    def get_hashes(filename):
        """Function gets all hashes from a filename"""
        if not os.path.exists(filename):
            return None
        hashed_file = FileHelper.get_file_content(filename, "rb").split()
        hashed_file = [x for x in hashed_file if "hashed_file" not in x]
        return hashed_file

    @staticmethod
    def hash_postupgrade_file(verbose, dirname, check=False):
        """
        The function creates hash file over all scripts in postupgrade.d directory.

        In case of remediation it checks whether checksums are different and
        print what scripts were changed.
        """
        if not os.path.exists(dirname):
            message = 'Directory %s does not exist for creating checksum file'
            log_message(message, settings.postupgrade_dir, level=logging.ERROR)
            return

        postupg_scripts = PostupgradeHelper.get_all_postupgrade_files(verbose, dirname)
        if not postupg_scripts:
            return

        filename = settings.base_hashed_file
        if check:
            filename = settings.base_hashed_file + "_new"
        lines = []
        for post_name in postupg_scripts:
            lines.append(post_name + "=" + PostupgradeHelper.get_hash_file(post_name, sha1())+"\n")

        full_path_name = os.path.join(dirname, filename)
        FileHelper.write_to_file(full_path_name, "wb", lines)

        if check:
            hashed_file = PostupgradeHelper.get_hashes(os.path.join(dirname, settings.base_hashed_file))
            if hashed_file is None:
                message = 'Hashed_file is missing. Postupgrade scripts will not be executed'
                log_message(message, level=logging.WARNING)
                return False
            hashed_file_new = PostupgradeHelper.get_hashes(full_path_name)
            different_hashes = list(set(hashed_file).difference(set(hashed_file_new)))
            for file_name in [settings.base_hashed_file, filename]:
                os.remove(os.path.join(dirname, file_name))
            if different_hashes or len(different_hashes) > 0:
                message = 'Checksums are different in these postupgrade scripts: %s'
                log_message(message % different_hashes, level=logging.WARNING)
                return False
        return True

    @staticmethod
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


class OpenSCAPHelper(object):

    def __init__(self, result_dir, result_name, xml_result_name, html_result_name, content, third_party=None):
        self.binary = [settings.openscap_binary]
        self.result_dir = result_dir
        self.third_party = third_party
        self.xml_result_name = xml_result_name
        self.html_result_name = html_result_name
        self.result_name = result_name
        self.content = content

    def update_variables(self, result_dir, result_name, xml_result_name, html_result_name, content, third_party=None):
        self.result_dir = result_dir
        self.third_party = third_party
        self.xml_result_name = xml_result_name
        self.html_result_name = html_result_name
        self.result_name = result_name
        self.content = content

    @staticmethod
    def get_xsl_stylesheet():
        """Return full XSL stylesheet path"""
        return os.path.join(settings.share_dir, "preupgrade", "xsl", settings.xsl_sheet)

    @staticmethod
    def get_command_generate():
        if not SystemIdentification.get_system():
            command_generate = ['xccdf', 'generate', 'custom']
        else:
            command_generate = ['xccdf', 'generate', 'report']
        return command_generate

    def build_generate_command(self, xml_file, html_file):
        """Function builds a command for generating results"""
        command = [settings.openscap_binary]
        command.extend(OpenSCAPHelper.get_command_generate())
        if not SystemIdentification.get_system():
            command.extend(("--stylesheet", OpenSCAPHelper.get_xsl_stylesheet()))
        command.extend(("--output", html_file))
        command.append(FileHelper.check_xml(xml_file))
        return command

    def build_command(self):
        """create command from configuration"""
        command_eval = ['xccdf', 'eval']
        result_file = self.get_default_xml_result_path()
        command = [settings.openscap_binary]
        report = self.get_default_html_result_path()
        command.extend(command_eval)
        command.append('--progress')
        command.extend(('--profile', settings.profile))

        command.extend(("--results", result_file))
        command.append(FileHelper.check_xml(self.content))
        return command

    @staticmethod
    def get_third_party_name(third_party):
        """Function returns correct third party name"""
        if third_party != "" and not third_party.endswith("_"):
            third_party += "_"
        return third_party

    def get_default_xml_result_path(self):
        """Returns full XML result path"""
        return os.path.join(self.result_dir,
                            OpenSCAPHelper.get_third_party_name("") + self.xml_result_name)

    def get_default_html_result_path(self):
        """Returns full HTML result path"""
        return os.path.join(self.result_dir,
                            OpenSCAPHelper.get_third_party_name("") + self.html_result_name)

    @staticmethod
    def get_default_txt_result_path(self):
        """
        Function returns default txt result path based on result_dir

        :return: default txt result path
        """
        return os.path.join(self.result_dir,
                            OpenSCAPHelper.get_third_party_name("") + self.result_name + ".txt")


