# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required as lr

from .views import *

urlpatterns = patterns('',
    url(r'^$', lr(SettingsView.as_view()), name='settings'),
    url(r'^state/$', lr(SetStateSettingsView.as_view()), name='update-state-filter'),
)
