# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required as lr

from .views import RunsView, ReportView, NewRunView, NewHostView, DeleteOlderView, \
    NewLocalRunView, ReportFilesView, RunView, DeleteRunView, ResultViewAjax

urlpatterns = patterns(
    '',
    url(r'^$', lr(RunsView.as_view()), name='index'),
    url(r'^$', lr(RunsView.as_view()), name='results-list'),
    url(r'^delete-older/$', lr(DeleteOlderView.as_view()), name='delete-older'),
    url(r'^(?P<result_id>\d+)/detail/$', lr(RunView.as_view()), name='result-detail'),
    #url(r'^run/(?P<run_id>\d+)/$', lr(RunView.as_view()), name='run'),
    # TODO: creating runs from UI is not done and ready for production
    #url(r'^new/$', lr(NewRunView.as_view()), name='new-run'),
    #url(r'^new-local-run/$', lr(NewLocalRunView.as_view()), name='new-local-run'),
    #url(r'^new-host/$', lr(NewHostView.as_view()), name='new-host'),
    url(r'^(?P<result_id>\d+)/report/$', lr(ReportView.as_view()),  name='show-report'),
    url(r'^(?P<result_id>\d+)/file/$', lr(ReportFilesView.as_view()),        name='show-file'),
    url(r'^(?P<result_id>\d+)/ajax/$', lr(ResultViewAjax.as_view()), name='show-result-ajax'),
    url(r'^(?P<result_id>\d+)/delete/$', lr(DeleteRunView.as_view()), name='result-delete'),
)
