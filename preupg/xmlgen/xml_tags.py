from __future__ import unicode_literals
TAG_GROUP = "xccdf_preupg_group_"
TAG_VALUE = "xccdf_preupg_value_"
TAG_RULE = "xccdf_preupg_rule_"
GROUP_INI = """<xf:xccdf-fragment xmlns="http://checklists.nist.gov/xccdf/1.2"
 xmlns:xf="http://preupgrade-assistant.org/wiki/XCCDF-fragment"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">
    <Group id=\""""+TAG_GROUP+"""{main_dir}" selected="true">
    <title>{group_title}</title>
    {group_value}
    </Group>
</xf:xccdf-fragment>
"""

CONTENT_INI = """<xf:xccdf-fragment xmlns="http://checklists.nist.gov/xccdf/1.2"
 xmlns:xf="http://preupgrade-assistant.org/wiki/XCCDF-fragment"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">
    <Profile id="xccdf_preupg_profile_default">
        {select_rules}
    </Profile>
    <Group id=\""""+TAG_GROUP+"""{main_dir}" selected="true">
    <title>{group_title}</title>
    {group_value}
    {rule_tag}
    </Group>
</xf:xccdf-fragment>
"""
SELECT_TAG = """<select idref=\""""+TAG_RULE+"""{main_dir}_{scap_name}\" selected="true" />"""

VALUE = """
    <Value id=\""""+TAG_VALUE+"""{main_dir}_{scap_name}_state_{val}" operator="equals" type="string">
        <value>{value_name}</value>
    </Value>
"""
RULE_SECTION = """
    <Rule id=\""""+TAG_RULE+"""{main_dir}_{scap_name}" selected="true">
      <title>{content_title}</title>
      <description>
        {content_description}
        {check_description}
        {config_section}
      </description>
      <fixtext>{solution_text}</fixtext>
      <check system="http://open-scap.org/page/SCE">
        <check-import import-name="stdout" />
        {check_export}
        <check-content-ref href="{check_script}" />
      </check>
    </Rule>
"""
CONFIG_SECTION = """
        <xhtml:p>
            File(s) affected:
            <xhtml:ul>
            {config_file}
            </xhtml:ul>
        </xhtml:p>
"""
RULE_SECTION_VALUE_IMPORT = """\t\t<check-import import-name="stderr"/>"""

RULE_SECTION_VALUE = """\t\t<check-export export-name="{value_name_upper}" value-id=\""""+TAG_VALUE+"""{main_dir}_{scap_name}_state_{val}" />
"""
DIC_VALUES = {'current_directory': '/root/preupgrade',
              'module_path': '',
              }

GLOBAL_DIC_VALUES = {'tmp_preupgrade': 'SCENARIO',
                     'migrate': '0',
                     'upgrade': '0',
                     'report_dir': '/root/preupgrade',
                     'devel_mode': '0',
                     'dist_native': ''
                     }

RULE_SECTION_VALUE_GLOBAL = """\t\t<check-export export-name="{value_name_upper}" value-id=\""""+TAG_VALUE+"""{value_name}" />
"""
