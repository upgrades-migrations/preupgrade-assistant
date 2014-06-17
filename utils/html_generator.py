import ConfigParser
import jinja2
import xmlrpclib
import re
from textwrap import wrap
from jinja2 import Environment, FileSystemLoader
from utils.oscap_group_xml import *
from utils.script_utils import get_script_type, get_file_content
from preup.utils import write_to_file

try:
    import bugzilla
except ImportError:
    print "missing bugzilla module, please install it (yum install python-bugzilla)"
    sys.exit(1)

REPORT_NAME = "qa_report.html"
TEMPLATE_DIR = "templates"
RESULT_FILE = os.path.join(os.path.dirname(__file__), "..", REPORT_NAME)
# PRODUCTION "https://bugzilla.redhat.com/xmlrpc.cgi"
REPO_NAME = "http://git.app.eng.bos.redhat.com/git/preupgrade-assistant-contents-users.git/tree/"


def get_templates():
    return os.path.join(os.path.dirname(__file__), "..", TEMPLATE_DIR)


class HtmlGenerator(object):
    def __init__(self, ini_files, bz):
        self.ini_files = ini_files
        self.loaded_ini = {}
        self.report_data = []
        self.template_var = {}
        self.bz = bz

    def get_bz_status(self, bug):
        bz_url = self.bz.url.rsplit('/', 1)[0]

        try:
            b = self.bz.getbug(bug)
        except xmlrpclib.Fault as ex:
            print "Couldn't create requested bug, the error was: '%s'" % ex
            return None
        else:
            if hasattr(b, 'status'):
                return getattr(b, 'status')
            else:
                return None

    def get_content_path(self, key):
        return os.path.join(os.path.dirname(__file__), "..", os.path.dirname(key))

    def get_bugzilla_status(self, val, key):
        bug_status = {}
        for bug in filter(lambda x: x.strip(), val['bugzilla'].split(',')):
            status = self.get_bz_status(bug)
            bug_status[bug] = status if status is not None else ""
        val['bugzilla'] = bug_status
        return val

    def get_solution_text(self, val, key):
        solution_file = os.path.join(self.get_content_path(key), val['solution'])
        if get_script_type(key, script_name=solution_file) == "txt":
            val['solution'] = '<br/>'.join(wrap(get_file_content(solution_file, "r"), 200))
        else:
            del val['solution']
        return val

    def get_check_script(self, val, key):
        matched = re.search(r'.*contents-users\/(.*)', self.get_content_path(key), re.I)
        if matched:
            val['check_script_full'] = REPO_NAME+matched.group(1)+"/"+val['check_script']
        else:
            del val['check_script']
        return val

    def get_key(self, val, name):
        try:
            return val[name]
        except KeyError as ke:
            return ""

    def generate_template_vars(self):
        titles = []
        full_contents = {}
        for key, val in sorted(self.loaded_ini.iteritems()):
            print "Processing {0} ...".format(key),
            title = self.get_key(val, 'applies_to')
            title += " - " if title != "" else ""
            title += self.get_key(val, 'content_title')
            try:
                titles.append(title)
                if 'bugzilla' in val:
                    val = self.get_bugzilla_status(val, key)
                if 'solution' in val:
                    val = self.get_solution_text(val, key)
                if 'check_script' in val:
                    val = self.get_check_script(val, key)
                full_contents[title] = val
            except KeyError as ke:
                continue
            print 'done'
        self.template_var['contents'] = titles
        self.template_var['full_contents'] = full_contents

    def parse_inifiles(self):
        for d, f in self.ini_files.iteritems():
            try:
                config = ConfigParser.ConfigParser()
                config.readfp(open(os.path.join(d, f)))
                fields = {}
                if config.has_section(section_premigrate):
                    section = section_premigrate
                else:
                    section = section_preupgrade
                for option in config.options(section):
                    fields[option] = config.get(section, option).decode('utf-8')
                self.loaded_ini[os.path.join(d, f)] = fields
            except ConfigParser.MissingSectionHeaderError, e:
                print_error_msg(title="Missing section header")

    def generate_html(self):
        self.parse_inifiles()
        self.generate_template_vars()
        env = Environment(loader=FileSystemLoader(get_templates()))
        template = env.get_template('qa_template.html')
        output = template.render(self.template_var).encode('utf-8')
        write_to_file(RESULT_FILE, "w", output)
        print 'HTML file: {0}'.format(RESULT_FILE)

