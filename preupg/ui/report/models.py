# -*- coding: utf-8 -*-
""" Database schema """
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.aggregates import Count
from django.http.response import Http404
import os
import datetime

from django.db import models
from django.conf import settings
from preupg.ui.config.models import AppSettings
from preupg.ui.utils.enum import Enum
from shutil import rmtree


class OS(models.Model):
    RHEL5 = 5
    RHEL6 = 6
    RHEL7 = 7

    MAJOR_VERSIONS = Enum([
        (RHEL5, 'RHEL-5', 'Red Hat Enterprise Linux 5'),
        (RHEL6, 'RHEL-6', 'Red Hat Enterprise Linux 6'),
        (RHEL7, 'RHEL-7', 'Red Hat Enterprise Linux 7'),
    ])
    major = models.SmallIntegerField(choices=MAJOR_VERSIONS.get_mapping())
    minor = models.SmallIntegerField()

    class Meta:
        ordering = ('major', 'minor')

    def __unicode__(self):
        return u"%s.%d" % (self.MAJOR_VERSIONS.get_help(self.major),
                           self.minor)


class Host(models.Model):
    """
    host where analysis was executed
    creds are required for distributive execution
    """
    hostname = models.CharField(max_length=255)
    ssh_name = models.CharField(max_length=255, blank=True, null=True)
    # TODO: security \/
    ssh_password = models.CharField(max_length=255, blank=True, null=True)
    sudo_password = models.CharField(max_length=255, blank=True, null=True)
    su_login = models.CharField(max_length=255, blank=True, null=True,
                                help_text="Alternative user")
    local = models.BooleanField(default=False, help_text="Local analysis")

    os = models.ForeignKey(OS, blank=True, null=True)

    class Meta:
        ordering = ('hostname',)

    def __unicode__(self):
        return u"%s (%s)" % (self.hostname, self.os)

    @classmethod
    def localhost(cls):
        return cls.objects.get(hostname="localhost")


class TestGroupMixin(object):
    def create_or_update(self, k):
        """
        return Test object for specified id_ref rule
        """
        try:
            tg = self.get(xccdf_id=k['xccdf_id'])
        except ObjectDoesNotExist:
            tg = TestGroup(**k)
            tg.save()
        else:
            self.filter(pk=tg.pk).update(**k)
        return tg

    def root(self):
        return self.filter(parent__isnull=True)


class TestGroupQuerySet(models.query.QuerySet, TestGroupMixin):
    pass


class TestGroupManager(models.Manager, TestGroupMixin):
    def get_query_set(self):
        return TestGroupQuerySet(self.model, using=self._db)


class TestGroup(models.Model):
    """
    Tests are composed into groups, user may pick which groups to choose
    """
    title = models.CharField(max_length=255, db_index=True)
    xccdf_id = models.CharField(max_length=128)
    parent = models.ForeignKey('self', blank=True, null=True)

    objects = TestGroupManager()

    class Meta:
        ordering = ('title', )

    def __unicode__(self):
        if self.parent:
            return u"%s [%s]" % (self.title, self.parent)
        else:
            return u"%s" % (self.title)

    def has_children(self):
        return TestGroup.objects.filter(parent=self).exists()

    def children(self):
        return TestGroup.objects.filter(parent=self)

    def is_root(self):
        """ is this group root group? == does it have parent? """
        return self.parent is None


class TestGroupResultMixin(object):
    def for_result(self, result):
        return self.filter(result=result)

    def search_in_title(self, query_string):
        return self.filter(group__title__icontains=query_string)

    def root(self):
        return self.filter(parent__isnull=True)


class TestGroupResultQuerySet(models.query.QuerySet, TestGroupResultMixin):
    pass


class TestGroupResultManager(models.Manager, TestGroupResultMixin):
    def get_query_set(self):
        return TestGroupResultQuerySet(self.model, using=self._db)


class TestGroupResult(models.Model):
    """
    Result of test group -- combine run and testgroup together
    """
    group = models.ForeignKey(TestGroup)
    result = models.ForeignKey('Result')
    parent = models.ForeignKey('self', related_name="direct_children_set", blank=True, null=True)
    # this should never be None, but if this group is root also, it has to be saved first
    root = models.ForeignKey('self', related_name="all_children_set", blank=True, null=True)

    test_count = models.SmallIntegerField(blank=True, null=True, default=0)
    failed_test_count = models.SmallIntegerField(blank=True, null=True, default=0)
    ni_test_count = models.SmallIntegerField(blank=True, null=True, default=0)
    na_test_count = models.SmallIntegerField(blank=True, null=True, default=0)

    objects = TestGroupResultManager()

    class Meta:
        ordering = ('group', )

    def __unicode__(self):
        return u"%s %s" % (self.group, self.result)

    def has_children(self):
        return TestGroupResult.objects.filter(parent=self).exists()

    def children(self):
        return TestGroupResult.objects.filter(parent=self)

    def testresults(self):
        return self.testresult_set.all()

    def get_root(self):
        """ return root group -- top-most parent """
        if self.root is not None:
            return self.root
        group = self
        parent = self.parent
        while parent is not None:
            group = parent
            parent = group.parent
        self.root = group
        self.save()
        return group

    #def title_matches_filter(self, search_string):
    #    """ does this group matches searching? """
    #    return search_string.lower() in self.group.title


class RunMixin(object):

    def create_for_host(self, host):
        run = Run()
        run.save()
        HostRun.objects.create(host=host, run=run)
        return run

    def bulk_create_for_run(self, hosts):
        """
        create hostruns for list of hosts specified as Query in variable hosts
        """
        run = Run()
        run.save()
        hostrun_list = []
        for host in hosts:
            hostrun_list.append(HostRun(host=host, run=run))

        HostRun.objects.bulk_create(hostrun_list)
        return run


class RunQuerySet(models.query.QuerySet, RunMixin):
    pass


class RunManager(models.Manager, RunMixin):
    def get_query_set(self):
        return RunQuerySet(self.model, using=self._db)


class Run(models.Model):
    """
    one run may consist of several results (from multiple hosts)
    """
    dt_submitted = models.DateTimeField(auto_now_add=True)
    dt_finished = models.DateTimeField(blank=True, null=True)
    objects = RunManager()

    class Meta:
        ordering = ('-dt_submitted', )

    def __unicode__(self):
        if not self.dt_finished:
            return u"#%d %s (running)" % (self.id, self.dt_submitted)
        else:
            return u"#%d %s--%s" % (self.id, self.dt_submitted,
                                    self.dt_finished)

    def results(self):
        """ Return all Results from this run"""
        return Result.objects.filter(hostrun__run=self)

    def testresults(self):
        """ Return all TestResults from this run"""
        return TestResult.objects.filter(group__result__hostrun__run=self)

    def get_run_dir(self):
        results_dir = os.path.abspath(settings.RESULTS_DIR)
        path = os.path.join(results_dir, str(self.id))
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o0755)
        return path

    def has_local(self):
        """ should there be some scan performed locally? """
        return self.hostrun_set.filter(host__local=True).exists()

    def local(self):
        """ return local hostrun assigned to this run """
        return HostRun.objects.get(run=self, host__local=True)

    def remotes(self):
        """ Return remote HostRuns """
        return HostRun.objects.filter(run=self, host__local=False)

    def all_done(self):
        """ if there are no running tasks, everything is done """
        return not HostRun.objects.for_run(self).running().exists()

    def finish(self):
        self.dt_finished = datetime.datetime.now()
        self.save(update_fields=["dt_finished"])

    def first_hostrun(self):
        return self.hostrun_set.all()[0]


class HostRunMixin(object):
    def for_run(self, run):
        return self.filter(run=run)

    def for_result(self, result_id):
        result = self.filter(result=result_id)
        if not result:
            raise Http404('There is no such run.')
        else:
            return result

    def running(self):
        return self.filter(state=HostRun.RUNNING)

    def finished(self):
        return self.filter(state=HostRun.FINISHED)

    def hosts(self):
        """ return list of hostname strings found in hostruns """
        return self.values_list("result__hostname", flat=True)

    def risks(self):
        """ return list of risk strings found in hostruns """
        return self.values_list("risk", flat=True).distinct()

    def by_risk(self, risk):
        return self.filter(risk=risk)

    def by_hosts_processed(self, hosts):
        return self.filter(result__hostname__in=hosts)


class HostRunQuerySet(models.query.QuerySet, HostRunMixin):
    pass


class HostRunManager(models.Manager, HostRunMixin):
    def get_query_set(self):
        return HostRunQuerySet(self.model, using=self._db)


class HostRun(models.Model):
    """
    M2M relationship between run and hosts -- Run on each Host
    """
    RUNNING = 'r'
    FINISHED = 'f'

    RUN_STATES = Enum([
        (RUNNING, 'running', 'Scan is active.'),
        (FINISHED, 'finished', 'Scan has finished.'),
    ])
    dt_finished = models.DateTimeField(blank=True, null=True)
    host = models.ForeignKey(Host)
    run = models.ForeignKey(Run)
    state = models.CharField(max_length=1, choices=RUN_STATES.get_mapping(), default=RUNNING, db_index=True)
    risk = models.CharField(max_length=16, blank=True, null=True, db_index=True)

    objects = HostRunManager()

    def __unicode__(self):
        return u"%s %s %s" % (self.get_state_display(), self.host, self.run)

    class Meta:
        ordering = ('-run__dt_submitted', )

    @property
    def running(self):
        return self.state == self.RUNNING

    @property
    def finished(self):
        return self.state == self.FINISHED

    def display_groups(self):
        return self.testgroupresult.filter(parent__isnull=True)

    def set_finished(self):
        self.state = self.FINISHED
        self.dt_finished = datetime.datetime.now()
        self.save(update_fields=["state"])

    def set_risk(self):
        risks = Risk.objects.for_hostrun(self)
        risk = "Can't determine"
        if risks:
            risks_list = list(risks.values_list('level', flat=True).distinct())
            sorted_risks_list = sorted(risks_list, key=lambda x: Risk.RISK_LEVELS[x])
            risk = sorted_risks_list[-1]
        self.risk = risk
        self.save(update_fields=["risk"])

    def delete(self):
        if self.result:
            self.result.delete()
        super(HostRun, self).delete()


class Result(models.Model):
    """ report with results """
    dt_submitted = models.DateTimeField(blank=True, null=True)
    dt_finished = models.DateTimeField(blank=True, null=True)
    # html report
    filename = models.CharField(max_length=128, blank=True, null=True)
    hostrun = models.OneToOneField(HostRun)
    identity = models.CharField(max_length=255, blank=True, null=True)
    # hostname from results
    hostname = models.CharField(max_length=255, blank=True, null=True)

    test_count = models.SmallIntegerField(blank=True, null=True)
    failed_test_count = models.SmallIntegerField(blank=True, null=True)
    ni_test_count = models.SmallIntegerField(blank=True, null=True)
    na_test_count = models.SmallIntegerField(blank=True, null=True)

    def delete(self):
        result_dir = self.get_result_dir()
        super(Result, self).delete()
        rmtree(result_dir)

    def __unicode__(self):
        return u"%s (%s)" % (self.hostname, self.dt_finished)

    def get_file_path(self):
        return os.path.join(self.get_result_dir(), self.filename)

    def get_result_dir(self):
        run_dir = self.hostrun.run.get_run_dir()
        path = os.path.join(run_dir, str(self.id))
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o0755)
        return path

    @property
    def results(self):
        return self.testresult_set.all()

    def status_text(self):
        result = []
        results_dict = TestResult.objects.for_result(self).count_states()
        for test in results_dict:
            test_print = "%s (%d)" % (
                TestResult.TEST_STATES.display(test['state']),
                test['count'],
            )
            result.append(test_print)
        return ', '.join(result)

    @property
    def groups(self):
        return self.testgroupresult_set.all()

    def root_groups(self):
        return self.testgroupresult_set.filter(group__parent__isnull=True)

    def states(self):
        """ return dict with states of tests in this run """

        result = {}

        for r in TestResult.objects.for_result(self).count_states():
            printable_state = TestResult.TEST_STATES.display(r['state'])
            print_text = "%s (%d)" % (printable_state, r['count'])
            result[TestResult.TEST_STATES[r['state']]] = print_text
            # e.g. {'fixed': 'Fixed (8)'}
        return result


class Address(models.Model):
    address = models.GenericIPAddressField()
    result = models.ForeignKey(Result)

    def __unicode__(self):
        return u"%s [%s]" % (self.address, self.result)


class TestMixin(object):
    def create_or_update(self, k):
        """
        return Test object for specified id_ref rule
        """
        try:
            test = self.get(id_ref=k['id_ref'])
        except ObjectDoesNotExist:
            test = Test(**k)
            test.save()
        else:
            self.filter(pk=test.pk).update(**k)
        return test


class TestQuerySet(models.query.QuerySet, TestMixin):
    pass


class TestManager(models.Manager, TestMixin):
    def get_query_set(self):
        return TestQuerySet(self.model, using=self._db)


class Test(models.Model):
    """ this model matches Rule of XCCDF """
    title = models.CharField(max_length=255, db_index=True)
    # rule's idref -- unique name of test within report
    id_ref = models.CharField(max_length=255)
    description = models.TextField()
    component = models.CharField(max_length=128, null=True, blank=True)
    # script for fixing
    fix = models.TextField(null=True, blank=True)
    fix_type = models.CharField(max_length=32, null=True, blank=True)
    fixtext = models.TextField(null=True, blank=True)
    group = models.ForeignKey(TestGroup, blank=True, null=True)
    objects = TestManager()

    def __unicode__(self):
        return u"%s %s" % (self.id_ref, self.title)


class TestResultMixin(object):
    def failed(self):
        return self.filter(state=TestResult.FAILURE)

    def ni(self):
        """ needs inspection """
        return self.filter(state=TestResult.NEEDS_INSPECTION)

    def na(self):
        """ needs action """
        return self.filter(state=TestResult.NEEDS_ACTION)

    def by_state(self, state):
        # TODO add validation if state is valid
        return self.filter(state=state)

    def by_states(self, states):
        # TODO add validation if state is valid
        return self.filter(state__in=states)

    def for_tgr(self, group):
        return self.filter(group=group)

    def search_in_title(self, search_string):
        return self.filter(test__title__icontains=search_string)

    def for_result(self, result):
        return self.filter(group__result=result)

    def count_states(self):
        """ return states with counts for current query """
        return self.values('state').annotate(count=Count('state'))


class TestResultQuerySet(models.query.QuerySet, TestResultMixin):
    pass


class TestResultManager(models.Manager, TestResultMixin):
    def get_query_set(self):
        return TestResultQuerySet(self.model, using=self._db)


class TestResult(models.Model):
    """ this model represents rule-result """
    # order, shortcut of the state
    PASSED = '06p'  # (p)assed
    WARNING = '03w'  # (w)arning
    FAILURE = '02f'  # (f)ailure
    NEEDS_INSPECTION = '03ni'  # (n)eeds (i)nspection
    NEEDS_ACTION = '03na'  # (n)eeds (a)ction
    ERROR = '01e'  # (e)rror
    NOTAPPLICABLE = '07n'  # (n)otapplicable
    NOTCHECKED = '08c'  # not(c)hecked
    INFO = '05i'  # (i)nfo
    FIXED = '04x'  # fi(x)ed

    TEST_STATES = Enum([
        # DB value, used in css/html, helper text, printable value
        (ERROR, 'error', 'Unexpected problem during analysis.', 'Error'),
        (FAILURE, 'fail', 'Test failed, some serious problems were found.', 'Failed'),
        (NEEDS_ACTION, 'needs_action', 'Issues found by this test should be resolved.', 'Needs Action'),
        (NEEDS_INSPECTION, 'needs_inspection', 'Issues found by this test should be inspected.', 'Needs Inspection'),
        (FIXED, 'fixed', 'Fixed.', 'Fixed'),
        (PASSED, 'pass', 'Test passed, no problems found.', 'Passed'),
        (INFO, 'informational', 'Test is only informative.', 'Informational'),
        (NOTAPPLICABLE, 'notapplicable', 'Test is not applicable.', 'Not Applicable'),
        #(WARNING, 'warning', 'Test passed but there are some issues.', 'warning'),
        (NOTCHECKED, 'notchecked', 'Test couldn\'t be run.', 'Not Checked'),
    ])
    state = models.CharField(max_length=3, choices=TEST_STATES.get_mapping(), db_index=True)
    date = models.DateTimeField()
    test = models.ForeignKey(Test)
    group = models.ForeignKey(TestGroupResult, related_name="testresult_set")
    root_group = models.ForeignKey(TestGroupResult, related_name="all_tests")
    # since groups are nested, there is no easy way to get to result from tr
    result = models.ForeignKey(Result)

    objects = TestResultManager()

    class Meta:
        ordering = ('state', )

    def __unicode__(self):
        return u"%s [%s] [%s]" % (self.get_state_display().upper(),
                                  self.test, self.group)

    def logs(self):
        return self.testlog_set.all()

    def risks(self):
        return self.risk_set.all()

    def set_state(self, state, save=True):
        self.state = self.TEST_STATES.get_key(state)
        if save:
            self.save()

    def get_state(self):
        return TestResult.TEST_STATES[self.state]

    def display_state(self):
        return TestResult.TEST_STATES.display(self.state)

    def should_display_solution(self):
        return self.get_state() not in ['pass', 'notapplicable']


class TestLogMixin(object):
    def bulk_create_logs(self, testlogs, result):
        """
        create hostruns for list of hosts specified as Query in variable hosts
        """
        testlog_list = []
        keys = ['date', 'level', 'message']

        for testlog in testlogs:
            testlog_dict = dict((key, testlog[key]) for key in keys if key in testlog)
            tl = TestLog(**testlog_dict)
            tl.result = result
            testlog_list.append(tl)
        TestLog.objects.bulk_create(testlog_list)


class TestLogQuerySet(models.query.QuerySet, TestLogMixin):
    pass


class TestLogManager(models.Manager, TestLogMixin):
    def get_query_set(self):
        return TestLogQuerySet(self.model, using=self._db)


class TestLog(models.Model):
    message = models.TextField()
    level = models.CharField(max_length=32)
    date = models.DateTimeField(null=True, blank=True)
    result = models.ForeignKey(TestResult)

    objects = TestLogManager()

    def __unicode__(self):
        return u"%s %s %s" % (self.level, self.date, self.message)


class RiskMixin(object):
    def for_hostrun(self, hostrun):
        risks_or = Q()
        risk_levels = Risk.RISK_LEVELS.keys()
        for r in risk_levels:
            risks_or |= Q(level=r)
        return self.filter(result__group__result__hostrun=hostrun).filter(risks_or)

    def bulk_create_logs(self, risks, result):
        """
        create risk objects in bulk: risks is a list of dicts
        """
        risks_list = []

        for risk in risks:
            tl = Risk(message=risk['message'], level=risk['level'].lower())
            tl.result = result
            risks_list.append(tl)
        Risk.objects.bulk_create(risks_list)


class RiskQuerySet(models.query.QuerySet, RiskMixin):
    pass


class RiskManager(models.Manager, RiskMixin):
    def get_query_set(self):
        return RiskQuerySet(self.model, using=self._db)


class Risk(models.Model):
    RISK_LEVELS = {
        "slight": 1,
        "medium": 2,
        "high": 3,
        "extreme": 4,
    }
    message = models.TextField()
    level = models.CharField(max_length=32)

    result = models.ForeignKey(TestResult)

    objects = RiskManager()

    def __unicode__(self):
        return u"%s %s" % (self.level, self.message)
