# -*- coding: utf-8 -*-

from django.views.generic import FormView, TemplateView, View
from django.views.generic.list import ListView

from .forms import ResultForm

from .difference import TwoComparator


class TwoCompareView(FormView, TemplateView):
    template_name = "compare/two.html"

    def get(self, request, *args, **kwargs):
        context = {'title': 'Run comparison'}
        if request.GET:
            form = ResultForm(request.GET)
            if form.is_valid():
                diff = TwoComparator(form.cleaned_data['left_result'],
                                     form.cleaned_data['right_result'])
                context['diff'] = diff.compare()
                context['left'] = form.cleaned_data['left_result']
                context['right'] = form.cleaned_data['right_result']
        else:
            form = ResultForm()

        context['form'] = form
        return self.render_to_response(context)
