# -*- coding: utf-8 -*-

from django import forms

from preupg.ui.report.models import Result


class ResultForm(forms.Form):
    left_result = forms.ModelChoiceField(queryset=Result.objects.order_by('-dt_finished'), required=True)
    right_result = forms.ModelChoiceField(queryset=Result.objects.order_by('-dt_finished'), required=True)

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)

        self.fields['left_result'].widget.attrs['class'] = "selectpicker compare-left-field"
        self.fields['left_result'].widget.attrs['data-live-search'] = "true"
        self.fields['right_result'].widget.attrs['class'] = "selectpicker compare-right-field"
        self.fields['right_result'].widget.attrs['data-live-search'] = "true"
