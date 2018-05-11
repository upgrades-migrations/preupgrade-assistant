
from __future__ import unicode_literals
import datetime
import os
import subprocess
from preupg.logger import settings, logger_report, log_message, logging


class ScanningHelper(object):

    @staticmethod
    def compare_data(row):
        """Function sorts a data output"""
        test_cases = {'error': '01',
                      'fail': '02',
                      'needs_action': '03',
                      'needs_inspection': '04',
                      'fixed': '05',
                      'informational': '06',
                      'pass': '07',
                      'notapplicable': '08',
                      'notchecked': '09'}
        try:
            dummy_title, dummy_rule_id, result = row.split(':')
        except ValueError:
            return '99'
        else:
            try:
                return test_cases[result]
            except KeyError:
                return '99'

    @staticmethod
    def format_rules_to_table(output_data, content):
        """Function format output_data to table"""
        if not output_data:
            # If output_data does not contain anything then do not print nothing
            return
        max_title_length = max(x for x in [len(l.split(':')[0]) for l in output_data]) + 5
        max_result_length = max(x for x in [len(l.split(':')[2]) for l in output_data]) + 2
        log_message(settings.result_text.format(content))
        message = '-' * (max_title_length + max_result_length + 4)
        log_message(message)
        for data in sorted(output_data, key=ScanningHelper.compare_data, reverse=True):
            try:
                title, dummy_rule_id, result = data.split(':')
            except ValueError:
                # data is not an information about processed test; let's log it as an error
                log_message(data, level=logging.ERROR)
            else:
                log_message(u"|%s |%s|" % (title.ljust(max_title_length),
                                          result.strip().ljust(max_result_length)))
        log_message(message)


class ScanProgress(object):
    """The class is used for showing progress during the scan check."""
    def __init__(self, total_count, debug):
        self.total_count = total_count
        self.current_count = 0
        self.output_data = []
        self.debug = debug
        self.names = {}
        self.list_names = []
        self.width_size = 0
        self.time = datetime.datetime.now()

    def get_full_name(self, count):
        """Function returns full name from dictionary"""
        try:
            key = self.list_names[count]
        except IndexError:
            return ''
        return self.names[key]

    @staticmethod
    def get_terminal_width():
        """
        Function returns terminal width

        :return:
        """
        cmd = ["stty", "size"]
        sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return int(sp.communicate()[0].split()[1])

    def _return_correct_msg(self, msg):
        if len(msg) > self.width_size:
            msg = msg[:self.width_size - 7] + '...'
        return msg

    def show_progress(self, stdout_data):
        """Function shows a progress of assessment"""
        try:
            self.width_size = ScanProgress.get_terminal_width()
        except IndexError:
            self.width_size = 80
        logger_report.debug(stdout_data.strip())
        xccdf_rule = ""
        dummy_result = ""
        try:
            xccdf_rule, dummy_result = stdout_data.strip().split(':')
        except ValueError:
            print (stdout_data)
            return
        self.output_data.append(u'{0}:{1}'.format(self.names[xccdf_rule], stdout_data.strip()))
        self.current_count += 1
        old_width = self.width_size
        self.width_size -= 21
        prev_msg = self._return_correct_msg(self.get_full_name(self.current_count - 1))
        self.width_size = old_width
        cur_msg = self._return_correct_msg(self.get_full_name(self.current_count))
        cnt_back = 7 + len(prev_msg) + 3
        curr_time = datetime.datetime.now()
        diff_time = curr_time - self.time
        msg = (u'%sdone    (%s) (time: %.2d:%.2ds)'
               % ('\b' * cnt_back,
                  prev_msg,
                  diff_time.seconds / 60,
                  diff_time.seconds % 60))
        log_message(msg, new_line=True)
        if self.total_count > self.current_count:
            msg = self._return_correct_msg(u'%.3d/%.3d ...running (%s)'
                                           % (self.current_count + 1,
                                              self.total_count,
                                              cur_msg))
            log_message(msg, new_line=False)
        self.time = datetime.datetime.now()

    def set_names(self, names):
        """
        Function sets names of each rule

        names have format:
                key= xccdf_preupg_...
                value = "Full description"
        """
        self.names = names
        self.list_names = sorted(names)

    def get_output_data(self):
        """Function gets an output data from oscap"""
        return self.output_data

    def update_data(self, changed_fields):
        """Function updates a data"""
        for index, row in enumerate(self.output_data):
            try:
                title, rule_id, dummy_result = row.split(':')
                logger_report.debug(row)
            except ValueError:
                continue
            else:
                result_list = [x for x in changed_fields if rule_id in x]
                if result_list:
                    self.output_data[index] = u"%s:%s:%s" % (title, rule_id, result_list[0].split(':')[1])
