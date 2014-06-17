# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from views import TwoCompareView

urlpatterns = patterns(
    '',
    url(r'^$', TwoCompareView.as_view(), name='compare'),
    url(r'^two-compare/$', TwoCompareView.as_view(), name='two-compare'),
)