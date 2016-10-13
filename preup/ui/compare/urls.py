# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required as lr
from .views import TwoCompareView

urlpatterns = patterns(
    '',
    url(r'^$', lr(TwoCompareView.as_view()), name='compare'),
    url(r'^two-compare/$', lr(TwoCompareView.as_view()), name='two-compare'),
)
