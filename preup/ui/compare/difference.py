# -*- coding: utf-8 -*-

"""
Import reports and figure out difference.
"""


class DifferenceItem(object):
    """
    runs may have several items which are different, each item is represented by this class

    E.g.

    |      Run 1      |     Run 2    |
    ----------------------------------
    | Test X          |              |
    |                 | Test Y       |
    | Test Z (failed) | Test Z (N/A) |


    Each line in this table is a DifferenceItem

    """
    def __init__(self):
        self.record = {}

    def add(self, **items):
        for item, value in items.iteritems():
            self.record[item] = value

    def display(self):
        return self.record


class TwoComparator(object):
    def __init__(self, left, right):
        self.left_result = left
        self.right_result = right
        self.diff = []

    def compare(self):
        left_tests = self.left_result.results.select_related().prefetch_related('testlog_set', 'risk_set', 'test')
        right_tests = self.right_result.results.select_related().prefetch_related('testlog_set', 'risk_set', 'test')

        left_mapping = {}
        for tr in left_tests:
            left_mapping[tr.test.id_ref] = tr
        right_mapping = {}
        for tr in right_tests:
            right_mapping[tr.test.id_ref] = tr

        for tr in left_tests:
            try:
                right_tr = right_mapping[tr.test.id_ref]
            except KeyError:
                di = DifferenceItem()
                di.add(left=tr)
                self.diff.append(di.display())
            else:
                if right_tr.state != tr.state:
                    di = DifferenceItem()
                    di.add(left=tr, right=right_tr)
                    self.diff.append(di.display())
        for tr in right_tests:
            try:
                left_mapping[tr.test.id_ref]
            except KeyError:
                di = DifferenceItem()
                di.add(right=tr)
                self.diff.append(di.display())
        return self.diff
