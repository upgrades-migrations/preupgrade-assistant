# -*- coding: utf-8 -*-

from django import forms
from preupg.ui.report.models import TestResult
from django.http import QueryDict

class GenericStateFilterForm(forms.Form):
    """ filter test results by their state """

    def __init__(self, *args, **kwargs):
        super(GenericStateFilterForm, self).__init__(*args, **kwargs)

        states = TestResult.TEST_STATES.get_display_mapping()

        self.fields['state'] = forms.MultipleChoiceField(choices=states, required=False)
        #if initial_list:
        #    qd = QueryDict('state=a', mutable=True)
        #    qd.setlist('state', initial_list)
        #    print qd
        #    print qd.getlist('state')
        #    self.fields['state'].initial = qd
