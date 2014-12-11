import sys
import os

"""
Configuration file, key names has to match values in cli.py
"""

if os.path.basename(sys.argv[0]) == "premigrate":
    prefix = "premigrate"
else:
    prefix = "preupgrade"
# dir where results of analysis are stored
result_dir = os.path.join("/root", prefix)

# Dir where tar balls are placed
tarball_result_dir = result_dir+"-results"

# base name of XML and HTML file with results
result_name = "result"

tarball_base = result_name + 's'
tarball_name = "preupg_" + tarball_base + "-%s.tar.gz"

xml_result_name = result_name + '.xml'
html_result_name = result_name + '.html'

# base name of custom xsl stylesheet
xsl_sheet = "preup.xsl"

share_dir = "/usr/share"
# sources delivered by preupgrade assistant package
source_dir = os.path.join(share_dir, prefix)

# dir where the cached logs are stored
cache_dir = "/var/cache/preupgrade"

# file where the lock file stored
lock_file = "/var/run/preupgrade.pid"

# dir with log files"
log_dir = "/var/log/preupgrade"

# dir where the postupgrade scripts are placed
postupgrade_dir = "postupgrade.d"

# dir with preupgrade-scripts which are executed before reboot and upgrade.
preupgrade_name = "preupgrade-scripts"
preupgrade_scripts = os.path.join(result_dir, preupgrade_name)

# dirtyconfig directory used by preupgrade assistant
dirty_conf_dir = 'dirtyconf'

# cleanconfig directory used by preupgrade assistant
clean_conf_dir = 'cleanconf'

# cleanconf directory used by preupgrade assistant
# xccdf profile
profile = "xccdf_preupg_profile_default"

# name of dir with common files
common_name = "common"

# default directory is /var/tmp/preupgrade/common
# absolute path to dir with common files
common_dir = os.path.join(share_dir, prefix, common_name)

# path to file with definitions of common scripts
common_script = os.path.join(common_dir, "scripts.txt")

# Addons dir for 3rdparty contents
add_ons = "3rdparty"

# Default content file
content_file = "all-xccdf.xml"

# prefix of tag in fccdf files
xccdf_tag = "xccdf_preupg_rule_"

#name of the hash file
base_hashed_file = "hashed_file"

# path to file with definitions of common scripts
post_script = os.path.join(common_dir, "post_scripts.txt")

#kickstart and postupgrade.d directories
preupgrade_dirs = ['etc', dirty_conf_dir, clean_conf_dir, 'kickstart', postupgrade_dir, 'common']


readme_files = {'README': 'README',
                'README.kickstart': os.path.join('kickstart', 'README'),
                }

# Used for autogeneration check script issues
autocomplete = True

# new state needs_inspection
needs_inspection = "needs_inspection"

# new state needs_action
needs_action = "needs_action"

# The full license text
license = """Preupgrade assistant performs system upgradability assessment
and gathers information required for successful operating system upgrade.
Copyright (C) 2013 Red Hat Inc.
{0}
<new_line>
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
<new_line>
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
<new_line>
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

warning_text = "The Preupgrade Assistant is a diagnostics tool \n" \
               "and does not perform the actual upgrade.\n" \
               "Make sure you back up your system and all of your data now,\n" \
               "before using the Upgrade Tool to avoid potential data loss."
assessment_text = "Assessment of the system, running checks / SCE scripts"
result_text = "Result table with checks and their results for %s:"
message = "We found some potential in-place upgrade risks.\n" \
          "Read the file %s for more details."
converter_message = "At least one of these converters (%s) needs to be installed."

text_converters = {'w3m': '{0} -T text/html -dump {1} > {2}',
                   'lynx': '{0} -nonumbers -nolist -force_html -dump -nolist -width=255 {1} > {2}',
                   'elinks': '{0} --no-references -dump-width 255 --no-numbering -dump {1} > {2}',
                   }

ui_command = "preupg -u http://127.0.0.1:8099/submit/ -r %s/preupg_results-*.tar.gz"
openssl_command = "openssl x509 -text -in %s | grep -A1 1.3.6.1.4.1.2312.9.1"

UPGRADE_PATH = ""
KS_DIR = os.path.join(result_dir, 'kickstart')
KS_TEMPLATE = os.path.join(KS_DIR, 'default.ks')
KS_TEMPLATE_POSTSCRIPT = os.path.join(KS_DIR, 'finish.sh')
KS_FILES = ['default_grouplist-el6', 'default-optional_grouplist-3']
PREUPGRADE_KS = os.path.join(result_dir, 'preupgrade.ks')