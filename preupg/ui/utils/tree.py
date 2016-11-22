# -*- coding: utf-8 -*-

from django.utils.datastructures import SortedDict
from preupg.ui.config.models import AppSettings
from preupg.ui.report.models import TestResult, TestGroupResult
from .views import get_states_to_filter


def get_groups_children(group, groups):
    """
    we want to operate on the same set of elements, so we can use caching
    """
    return [x for x in groups if x.parent and x.parent.id == group.id]


def get_groups_tests(group, tests):
    """
    we want to operate on the same set of elements, so we can use caching
    """
    return [x for x in tests if x.group.id == group.id]


class RecursiveFilter(object):
    """
    go through graph structure of groups and filter requested group.
    This creates new attributes on groups:
     \ filtered_tests -- filtered tests in this category only
     \ allfiltered_tests -- tests in this category and its children
    """
    def __init__(self, groups, tests):
        """ groups, tests are queries """
        self.groups = groups
        self.tests = tests
        self.test_ids = tests.values_list('id', flat=True)

    def testresults_filter(self, group):
        """ self.tests is already performed filter, lets grep tests matching provided group """
        if hasattr(group, 'filtered_tests'):
            return group.filtered_tests[:]
        groups_tests = get_groups_tests(group, self.tests)
        group.filtered_tests = []
        for groups_test in groups_tests:
            # django's lazy queries won't evaluate self.test_ids first time
            # if groups_test.id in self.test_ids:
            if groups_test.id in iter(self.test_ids):
                group.filtered_tests.append(groups_test)
        return group.filtered_tests[:]

    def subelements_filter(self, group):
        """
        recursively traverse to group's children and return all tests which will be displayed
        """
        if hasattr(group, 'allfiltered_tests'):
            return group.allfiltered_tests[:]

        allfiltered_tests = self.testresults_filter(group)

        for child in get_groups_children(group, self.groups):
            # and do the same for children
            allfiltered_tests += self.subelements_filter(child)
        group.allfiltered_tests = allfiltered_tests
        return allfiltered_tests[:]


class RecursiveRenderer(object):
    def __init__(self, groups_dict):
        """
        {
            'group': {
                'group': None,
                'group': None,
            },
            'group': None,
        }
        """
        self.groups = groups_dict
        self.result = []

    def _append_group(self, group):
        self.result.append(('GROUP', group))

    def _append_tag(self, tag):
        self.result.append(('TAG', tag))

    def _append_tests(self, group):
        """ in template, we use group.filtered_tests """
        self.result.append(('TESTS', group))

    def _append_group_with_tests(self, group):
        """ group has no subgroups, lets display it with tests at once """
        self.result.append(('GROUP_WITH_TESTS', group))

    def translate_groups(self, groups):
        """
        This recursive function renders this:
        <ul root-groups>
          <li>
            <group>
              <ul>
                <li>
                  <group>
                    <ul>
                      <tests>
                    </ul>
                </li>
                <li>
                  <group>
                    <ul>
                      <tests>
                    </ul>
                </li>
                <tests>
              </ul>
            <group>
          </li>
        </ul>
        """
        for group, children in groups.iteritems():
            # starting li tags for groups are in template, so the tag can be tweaked
            if children is None:
                # there are no children, display group with ite tests
                self._append_group_with_tests(group)
            else:
                # this is more complex scenario:
                # this group has subgroups and may have tests
                self._append_group(group)
                self._append_tag('<ul class="entry-list">')
                # lets display recursively children
                self.translate_groups(children)
                # subgroups precede tests of current group
                if group.filtered_tests:
                    self._append_tests(group)
                self._append_tag('</ul>')
            self._append_tag('</li>')

    def render(self):
        """
        return a list of tuples where first item of tuple is
        information of what is in second place:
            ({TAG,GROUP,TESTS}, <object>)
        """
        self.translate_groups(self.groups)
        return self.result


def render_result(result, search_string=None, get=None):
    filtering_active = bool(search_string or get)

    # convert states to those in DB
    state_filter = TestResult.TEST_STATES.list_keys(get_states_to_filter(get))
    if not state_filter:
        state_filter = TestResult.TEST_STATES.list_keys(AppSettings.get_initial_state_filter())

    # perform global queries in tests and groups; we'll use our caching for these
    groups = TestGroupResult.objects.for_result(result)
    root_groups = groups.root()
    tests = TestResult.objects.for_result(result).by_states(state_filter)
    if search_string:
        groups = groups.search_in_title(search_string)
        tests = tests.search_in_title(search_string)
    groups = groups.select_related('parent', 'group', 'group__parent')
    tests = tests.select_related().prefetch_related('testlog_set', 'risk_set')

    rf = RecursiveFilter(groups, tests)

    def is_requested(group, force=False):
        """
        lets put together the tree structure and check if there is anything to display in this group
        """
        count = len(rf.subelements_filter(group))

        if count > 0 or force:
            group.displayed_count = count
            return True
        return False

    def filter_children(children, level):
        """ recursively go through provided groups """
        ch_dict = SortedDict()
        for child in children:
            child.left_margin = level + 1
            child.child_left_margin = level + 2
            is_child_requested = is_requested(child, level == -1 and not filtering_active)

            if is_child_requested:
                groups_gchildren = get_groups_children(child, groups)
                if len(groups_gchildren) > 0:
                    ch_dict[child] = filter_children(groups_gchildren, level + 1)
                else:
                    ch_dict[child] = None
        return ch_dict

    if not filtering_active:
        root_groups = filter(lambda x: x.parent is None, groups)

    groups_dict = filter_children(root_groups, -1)

    result_list = RecursiveRenderer(groups_dict).render()

    return result_list
