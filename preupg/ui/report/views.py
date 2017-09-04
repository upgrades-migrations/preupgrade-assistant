# -*- coding: utf-8 -*-
import json
import logging
import traceback
from django.core.exceptions import ObjectDoesNotExist
from django.template.context import RequestContext
import os
from preupg.ui.config.models import AppSettings

from .models import Run, Result
from .forms import *

from django.views.generic import TemplateView, DeleteView, FormView, View
from django.views.generic.list import ListView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse, reverse_lazy
from preupg.ui.utils.tree import render_result
from preupg.ui.utils.views import is_state_filter, return_error, get_states_to_filter
from django.http.response import Http404
from django.template import loader


logger = logging.getLogger('preup_ui')


class RunsView(ListView):
    template_name = "report/runs.html"
    paginate_by = 25
    context_object_name = 'hostruns'

    def get_queryset(self):
        try:
            query = HostRun.objects.for_result(self.kwargs['result_id'])
        except KeyError:
            query = HostRun.objects.all()
        else:
            return query.select_related('result', 'run', 'host')
        if self.request.GET:
            filter_form = FilterForm(self.request.GET)
            if filter_form.is_valid():
                query = HostRun.objects.finished()
                if filter_form.cleaned_data['hosts']:
                    query = query.by_hosts_processed(filter_form.cleaned_data['hosts'])
                if filter_form.cleaned_data['risk']:
                    query = query.by_risk(filter_form.cleaned_data['risk'])
        query = query.select_related('result', 'run', 'host')
        return query

    def get_action_form(self):
        if self.request.method == 'POST':
            form = ListActionForm(data=self.request.POST)
        else:
            form = ListActionForm()
        form.fields['runs'].choices = [(r.id, r.id) for r in self.get_queryset()]
        return form

    def get_context_data(self, **kwargs):
        context = super(RunsView, self).get_context_data(**kwargs)
        if self.request.GET:
            filter_form = FilterForm(self.request.GET)
        else:
            filter_form = FilterForm()
        context['title'] = 'List of runs'
        context['filter_form'] = filter_form
        context['action_form'] = self.get_action_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_action_form()
        if form.is_valid():
            action = getattr(self, form.cleaned_data['action'])
            return action(form)
        else:
            return self.get(request, *args, **kwargs)

    def delete_selected(self, form):
        # TODO limit number of input values
        hostruns = HostRun.objects.filter(id__in=form.cleaned_data['runs'])
        if form.cleaned_data['confirm']:
            for hostrun in hostruns:
                hostrun.delete()
            return HttpResponseRedirect('{0}?{1}'.format(
                reverse('results-list'),
                self.request.META['QUERY_STRING'],
            ))
        else:
            return TemplateResponse(
                request  = self.request,
                template = 'report/hostrun_delete_selected.html',
                context  = {
                    'form':     form,
                    'hostruns': hostruns,
                },
            )


class DeleteOlderView(FormView):
    template_name   = 'report/hostrun_delete_older.html'
    form_class      = DeleteOlderForm

    def get_form_kwargs(self):
        # ensure that the form is always bound
        return {'data': self.request.REQUEST}

    def get_older_hostruns(self, form):
        hostname = form.is_valid() and form.cleaned_data['host']
        hostruns = HostRun.objects.all()
        if hostname:
            hostruns = hostruns.filter(host__hostname=hostname)
        previous_host_id = None
        for hostrun in hostruns.order_by('host', '-run__dt_submitted'):
            if hostrun.host_id == previous_host_id:
                yield hostrun
            previous_host_id = hostrun.host_id

    def get_context_data(self, **kwargs):
        context = super(DeleteOlderView, self).get_context_data(**kwargs)
        context['hostruns'] = self.get_older_hostruns(context['form'])
        return context

    def form_valid(self, form):
        for hostrun in self.get_older_hostruns(form):
            hostrun.delete()
        return HttpResponseRedirect('{0}?{1}'.format(
            reverse('results-list'),
            self.request.META['QUERY_STRING'],
        ))


class RunView(RunsView):
    template_name = "report/runs.html"

    def get_context_data(self, **kwargs):
        context = super(RunView, self).get_context_data(**kwargs)
        context['title'] = "Run's detail"
        context['filtered_results'] = [int(self.kwargs['result_id'])]
        context['detail'] = True
        context['is_paginated'] = False
        context['url'] = reverse('result-detail', kwargs={'result_id': self.kwargs['result_id']})
        return context


class DeleteRunView(DeleteView):
    model = HostRun
    success_url = reverse_lazy('results-list')
    pk_url_kwarg = 'result_id'


class ResultViewAjax(View):
    """ display specific result, this routine is for ajax"""

    def get(self, request, result_id, *args, **kwargs):
        try:
            result = Result.objects.get(id=result_id)
        except ObjectDoesNotExist:
            return HttpResponse(
                json.dumps({'status': 'ERROR', 'content': "Not found."}),
                content_type='application/json',
            )

        response = {}

        # form with states
        states = get_states_to_filter(request.GET)
        if states:
            form = StateFilterForm(request.GET, result=result)
            try:
                self.request.GET['filter'] == 'all'
            except KeyError:
                pass
            else:
                AppSettings.set_initial_state_filter(states)
        else:
            init_states = AppSettings.get_initial_state_filter()
            inital_conf = {}
            for i in init_states:
                key = i + str(result.id)
                inital_conf[key] = True
            form = StateFilterForm(result=result, initial=inital_conf)

        try:
            search_string = request.GET['search']
        except KeyError:
            search_string = ''

        context = RequestContext(request, {
            'flat_tree': render_result(result, search_string, request.GET),
            'result': result,
            'state_filter_form': form,
        })
        template_name = "report/result.html"
        template = loader.get_template(template_name)
        response['content'] = template.render(context)
        response['status'] = 'OK'
        return HttpResponse(
            json.dumps(response),
            content_type='application/json',
        )


class ReportFilesView(View):
    """ display arbitrary files from scan result """

    def dir_content_html(self, absolute_dir_path, relative_dir_path):
        """Create a simple HTML code containing links to the content of the
        passed directory.
        """
        def sort_dirs_first(filename):
            return (os.path.isfile(os.path.join(absolute_dir_path, filename)),
                    filename.lower())
        sorted_dir_content = sorted(os.listdir(absolute_dir_path),
                                    key=sort_dirs_first)
        content = "<html>\n"
        for filename in sorted_dir_content:
            absolute_filepath = os.path.join(absolute_dir_path, filename)
            file_type_indicator = \
                "DIR  " if os.path.isdir(absolute_filepath) else "FILE "
            relative_filepath = os.path.join(relative_dir_path, filename)
            content += \
                file_type_indicator + "<a href='../file/?path=" + \
                relative_filepath + "'>" + filename + "</a><br>\n"
        content += "</html>\n"
        return content

    def get(self, request, result_id):
        """
        There has to be GET: path='...'
        """
        r = get_object_or_404(Result, id=result_id)
        result_dir = r.get_result_dir()

        try:
            relative_file_path = request.GET['path']
        except KeyError:
            return return_error(request, "Can't open a file because there is"
                                         " no path specified.")

        if not relative_file_path:
            return return_error(request, "Can't open a file because file path"
                                         " is empty.")

        absolute_file_path = os.path.abspath(os.path.join(result_dir,
                                                          relative_file_path))

        if not absolute_file_path.startswith(result_dir):
            return return_error(request, "You are not allowed to access file"
                                         " '%s'." % relative_file_path)

        if os.path.isdir(absolute_file_path):
            response = HttpResponse(self.dir_content_html(absolute_file_path,
                                                          relative_file_path),
                                    mimetype='text/html')
        else:
            try:
                file_content = open(absolute_file_path, 'r')
            except IOError:
                raise Http404('Can\'t open file \'%s\'' % relative_file_path)
            response = HttpResponse(file_content, mimetype='text/plain')
            response["Content-Length"] = os.path.getsize(absolute_file_path)

        return response


class ReportView(View):
    """ display HTML report """
    def get(self, request, result_id):
        r = get_object_or_404(Result, id=result_id)
        file_path = r.get_file_path()

        try:
            f = open(file_path, 'r')
        except IOError:
            raise Http404('Can\'t open HTML report')
        response = HttpResponse(f, mimetype='text/html')

        response["Content-Length"] = os.path.getsize(file_path)

        # this will prompt for download
        #response['Content-Disposition'] = 'attachment; filename=%s' % \
        #    os.path.basename(r.filename)
        return response


class NewHostView(FormView, TemplateView):
    template_name = "report/new_run.html"

    def post(self, request, *args, **kwargs):
        nh_form = NewHostForm(request.POST)
        nr_form = NewRunForm()
        context = {'new_host_form': nh_form}
        context['new_run_form'] = nr_form

        if nh_form.is_valid():
            nh_form.save()
        return self.render_to_response(context)


class NewLocalRunView(FormView, TemplateView):
    template_name = "report/new_run.html"

    def get(self, request, *args, **kwargs):
        #localhost = Host.localhost()
        #run_object = Run.objects.create_for_host(localhost)
        from report.runner import run
        #run(request, run_object)
        try:
            run(request)
        except RuntimeError as ex:
            return return_error(request, str(ex))
        except Exception as ex:
            logger.critical(traceback.format_exc())
            return return_error(request, 'There was an error: \'%s\'' % str(ex))
        return HttpResponseRedirect(reverse('results-list'))


class NewRunView(FormView, TemplateView):
    template_name = "report/new_run.html"

    def post(self, request, *args, **kwargs):
        nh_form = NewHostForm()
        nr_form = NewRunForm(request.POST)
        context = {'new_host_form': nh_form}
        context['new_run_form'] = nr_form

        if nr_form.is_valid():
            run_object = Run.objects.bulk_create_for_run(nr_form.cleaned_data['hosts'])
            from report.runner import run
            run(run_object)
            return HttpResponseRedirect(reverse('results-list'))
        else:
            return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        context = {
            'new_host_form': NewHostForm(),
            'new_run_form': NewRunForm()
        }
        return self.render_to_response(context)
