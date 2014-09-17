# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import *


urlpatterns = patterns('',
    url(r'^$', SettingsView.as_view(), name='settings'),
    url(r'^state/$', SetStateSettingsView.as_view(), name='update-state-filter'),
)
