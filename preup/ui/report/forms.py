# -*- coding: utf-8 -*-
from django.db.models import Q

from django import forms

from .models import Host, HostRun, TestResult


class NewHostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewHostForm, self).__init__(*args, **kwargs)
        self.fields['ssh_name'].label = "SSH Login"
        self.fields['ssh_password'].label = "SSH Password"
        self.fields['sudo_password'].label = "sudo Password"
        self.fields['su_login'].label = "su Login"
        self.fields['local'].label = "Local scan"

    class Meta:
        model = Host


class NewRunForm(forms.Form):

    hosts = forms.ModelMultipleChoiceField(queryset=Host.objects.all())
    #tests = forms.ModelMultipleChoiceField(queryset=TestGroup.objects.all())

    def __init__(self, *args, **kwargs):
        super(NewRunForm, self).__init__(*args, **kwargs)
        self.fields['hosts'].label = "Hosts"


class FilterForm(forms.Form):
    """
    form displayed in the toolbar, you can filter runs by host, risk level or just plain search
    """
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={
            'id': 'global-search',
            'placeholder': "Search...",
            'class': 'form-control',
        })
    )
    hosts = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(
        attrs={
            'class': 'selectpicker global-filter host-filter',
            'data-live-search': 'true',
        })
    )
    risk = forms.ChoiceField(required=False, widget=forms.Select(
        attrs={
            'class': 'selectpicker global-filter risk-filter',
        })
    )


    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        risk_choices = []
        for risk in HostRun.objects.risks():
            if risk and risk not in risk_choices:
                risk_choices.append(risk)
        risk_choices = zip(risk_choices, [risk.capitalize() for risk in risk_choices])
        # first option searches in every release
        risk_choices.insert(0, ('', 'All Risk Levels'))
        self.fields['risk'].choices = risk_choices

        host_choices = [(hr['host__hostname'], hr['host__hostname'])
            for hr in HostRun.objects.values('host__hostname').order_by('host__hostname').distinct()
        ]
        # first option searches in every release
        host_choices.insert(0, ('', 'All Hosts'))
        self.fields['hosts'].choices = host_choices

    def is_valid(self):
        valid = super(FilterForm, self).is_valid()
        if not valid:
            return valid
        if not self.cleaned_data['hosts'] and not self.cleaned_data['risk'] and not self.cleaned_data['search']:
            return False
        return True

class StateFilterForm(forms.Form):
    """ filter test results by their state """

    def __init__(self, *args, **kwargs):
        result = kwargs.pop('result')
        super(StateFilterForm, self).__init__(*args, **kwargs)

        states = result.states()

        #states.insert(0, ('', 'All'))

        self.blacklisted_states = ['notchecked']

        sorted_mapping = sorted(TestResult.TEST_STATES.get_mapping(), key=lambda x: x[0])

        for state_key, state_css in sorted_mapping:
            try:
                print_state = states[state_css]
            except KeyError:
                if not TestResult.TEST_STATES[state_key] in self.blacklisted_states:
                    print_state = "%s (0)" % TestResult.TEST_STATES.display(state_key)
                else:
                    continue
            field_name = state_css + str(result.id)
            self.fields[field_name] = forms.BooleanField(label=print_state, required=False)
        #self.fields[field_name].widget.attrs['class'] = "state-filter"
        #self.fields[field_name].widget.attrs['multiple'] = "multiple"
        #try:
        #    initial = args[0]
        #except IndexError:
        #    pass
        #else:
        #    self.fields[field_name].initial = initial

    def all_checked(self):
        return len(self.initial) >= len(TestResult.TEST_STATES.get_mapping()) - len(self.blacklisted_states)


class ListActionForm(forms.Form):
    ACTIONS = {
        'delete_selected': 'Delete selected',
    }
    runs    = forms.MultipleChoiceField()
    action  = forms.ChoiceField(choices=ACTIONS.items())
    confirm = forms.BooleanField(required=False)


class DeleteOlderForm(forms.Form):
    host = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(DeleteOlderForm, self).__init__(*args, **kwargs)
        host_choices = [(hr['host__hostname'], hr['host__hostname'])
            for hr in HostRun.objects.values('host__hostname').order_by('host__hostname').distinct()
        ]
        self.fields['host'].choices = host_choices


