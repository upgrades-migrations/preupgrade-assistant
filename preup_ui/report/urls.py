# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import RunsView, ReportView, NewRunView, NewHostView, \
    NewLocalRunView, ReportFilesView, RunView, ResultViewAjax

urlpatterns = patterns(
    '',
    url(r'^$', RunsView.as_view(), name='index'),
    url(r'^$', RunsView.as_view(), name='results-list'),
    url(r'^(?P<result_id>\d+)/detail/$', RunView.as_view(), name='result-detail'),
    #url(r'^run/(?P<run_id>\d+)/$', RunView.as_view(), name='run'),
    # TODO: creating runs from UI is not done and ready for production
    #url(r'^new/$', NewRunView.as_view(), name='new-run'),
    #url(r'^new-local-run/$', NewLocalRunView.as_view(), name='new-local-run'),
    #url(r'^new-host/$', NewHostView.as_view(), name='new-host'),
    url(r'^(?P<result_id>\d+)/report/$', ReportView.as_view(),
        name='show-report'),
    url(r'^(?P<result_id>\d+)/file/$', ReportFilesView.as_view(),
        name='show-file'),

    url(r'^(?P<result_id>\d+)/ajax/$', ResultViewAjax.as_view(), name='show-result-ajax'),
)
