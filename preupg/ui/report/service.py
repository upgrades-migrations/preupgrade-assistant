# -*- coding: utf-8 -*-

import logging
import os
import datetime
import tarfile
import shutil

from .models import Test, TestResult, HostRun, Result, Address, TestLog, TestGroup, TestGroupResult
from .models import Risk

from processing import parse_xml_report, update_html_report

from django.db import transaction
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

logger = logging.getLogger('preup_ui')


def filter_files_by_ext(tar_content, ext, error_msg):
    try:
        return filter(lambda x: x.name.endswith(ext) and x.name.count('/') <= 1, tar_content)[0]
    except IndexError:
        raise Exception(error_msg)


def remove_upload(path):
    """ add exc handling & logging """
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(settings.MEDIA_ROOT):
        logger.error("Upload is not in MEDIA_ROOT, canceling cleanup process")
        return
    tb_dir = os.path.dirname(abs_path)
    if not os.path.samefile(settings.MEDIA_ROOT, tb_dir):
        shutil.rmtree(tb_dir)
    else:
        os.unlink(abs_path)


def extract_tarball(tbpath, target_dir):
    """ return report paths: (xml, html) """
    def strip_subfolder(tar_content):
        """The Web UI does not expect the subfolder in the extracted tarball
        content.
        """
        for member in tar_content:
            path_without_subfolder = member.path.split(os.sep)[1:]
            if path_without_subfolder:
                member.path = os.path.join(*member.path.split(os.sep)[1:])
                yield member

    tar = tarfile.open(tbpath)
    tar_content = tar.getmembers()
    tar.extractall(target_dir, strip_subfolder(tar_content))
    tar.close()

    xml = filter_files_by_ext(tar_content, '.xml',
                              'Missing XML report in tarball.')
    html = filter_files_by_ext(tar_content, '.html',
                               'Missing HTML report in tarball.')

    xml_path = os.path.join(target_dir, xml.name)
    html_path = os.path.join(target_dir, html.name)
    return xml_path, html_path


class ReportImporter(object):
    """
    Imports report on provided path to database
    """

    def __init__(self, tb_path, hostrun_id):
        """ create all required global DB models """
        self.tb_path = tb_path
        hostrun = get_object_or_404(HostRun, id=hostrun_id)
        self.hostrun = hostrun
        self.run = hostrun.run
        self.result = self._create_result()

        # initialized in execute_import -> process_tarball
        self.parsed_data = None
        # initialized in process_tarball
        self.html_path = None

    def _create_result(self):
        result = Result()
        result.hostrun = self.hostrun
        result.save()
        return result

    def _update_result(self):
        """ update result with data from report """
        def set_date(obj, field, key):
            try:
                setattr(obj, field, datetime.datetime.strptime(self.parsed_data[key], DATE_FORMAT))
            except KeyError:
                pass

        self.result.filename = os.path.basename(self.html_path)
        set_date(self.result, 'dt_submitted', 'started')
        set_date(self.result, 'dt_finished', 'finished')
        self.result.identity = self.parsed_data['identity']
        self.result.hostname = self.parsed_data['host']
        self.result.save()

    def _process_tarball(self):
        xml_path, html_path = extract_tarball(self.tb_path, self.result.get_result_dir())
        self.html_path = html_path
        remove_upload(self.tb_path)
        update_html_report(self.html_path)
        return parse_xml_report(xml_path)

    @transaction.commit_on_success
    def _add_to_db(self):
        """ add data to dabase """
        for address in self.parsed_data['addresses']:
            Address(address=address, result=self.result).save()

        test_keys = ['id_ref', 'title', 'description', 'fix', 'fix_type', 'fixtext']
        group_keys = ['xccdf_id', 'title', ]
        # cache of processed groups -- efficient way of assigning parents
        groups = {}
        for group in self.parsed_data['groups']:
            group_dict = dict((key, group[key]) for key in group_keys if key in group)
            if 'parent' in group:
                group_dict['parent'] = groups[group['parent']][0]
            tg = TestGroup.objects.create(**group_dict)

            trg = TestGroupResult()
            trg.group = tg
            trg.result = self.result
            if 'parent' in group:
                trg.parent = groups[group['parent']][1]
            trg.save()
            trg.root = trg.get_root()

            # save group and group result
            groups[group_dict['xccdf_id']] = (tg, trg)

            for rule in group['rules']:
                test_dict = dict((key, rule[key]) for key in test_keys if key in rule)
                test_dict['group'] = tg
                try:
                    # links in fixtext miss id of result, see report/processing.py stringify_children
                    test_dict['fixtext'] = test_dict['fixtext'].replace(
                        '__INSERT_URL__',
                        reverse('show-file', args=(self.result.id,))
                    )
                except KeyError:
                    pass
                t = Test.objects.create(**test_dict)

                tr = TestResult()
                try:
                    tr.set_state(rule['result'], False)
                except KeyError:
                    # rule wasn't selected probably
                    continue
                tr.date = datetime.datetime.strptime(rule['time'], DATE_FORMAT)
                tr.test = t
                tr.group = trg
                tr.result = self.result
                tr.root_group = trg.get_root()
                tr.save()

                # add logs to DB
                if 'logs' in rule:
                    TestLog.objects.bulk_create_logs(rule['logs'], tr)
                if 'risks' in rule:
                    Risk.objects.bulk_create_logs(rule['risks'], tr)

    def _calculate_group_stats(self):
        groups = []
        def recurs(parent, child):
            for gch in child.children():
                recurs(child, gch)
            child.failed_test_count += TestResult.objects.for_tgr(child).failed().count()
            child.ni_test_count += TestResult.objects.for_tgr(child).ni().count()
            child.na_test_count += TestResult.objects.for_tgr(child).na().count()
            child.test_count += TestResult.objects.for_tgr(child).count()
            if parent:
                parent.failed_test_count += child.failed_test_count
                parent.ni_test_count += child.ni_test_count
                parent.na_test_count += child.na_test_count
                parent.test_count += child.test_count
            groups.append(child)

        for group in self.result.groups:
            if group in groups:
                continue
            recurs(None, group)

        for group in groups:
            group.save()

    def _calculate_result_stats(self):
        self.result.test_count = TestResult.objects.for_result(self.result).count()
        self.result.failed_test_count = TestResult.objects.for_result(self.result).failed().count()
        self.result.na_test_count = TestResult.objects.for_result(self.result).na().count()
        self.result.ni_test_count = TestResult.objects.for_result(self.result).ni().count()
        self.result.save()

    def _calculate_stats(self):
        """
        calculate helpful stats functions, like sums
         -- this is best to be done, when everything's in DB
        """
        self._calculate_group_stats()
        self._calculate_result_stats()

    def execute_import(self):
        """ execute import itself, this is the main call """
        self.parsed_data = self._process_tarball()
        self._update_result()
        self._add_to_db()

        self.hostrun.set_finished()
        self.hostrun.set_risk()
        if self.run.all_done():
            self.run.finish()

        self._calculate_stats()


def import_report(tb_path, hostrun_id):
    ri = ReportImporter(tb_path, hostrun_id)
    ri.execute_import()


def main():
    pass


if __name__ == '__main__':
    main()
