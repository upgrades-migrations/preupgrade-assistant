# -*- coding: utf-8 -*-

from .views import *

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required as lr

# these are private URLs for auth management

urlpatterns = patterns('',
    url(r'^list/$', lr(AuthListView.as_view()), name='auth-list'),
    url(r'^create/$', lr(CreateUserView.as_view()), name='auth-create'),
    url(r'^enable/$', lr(EnableAuthView.as_view()), name='auth-enable'),
    url(r'^disable/$', lr(DisableAuthView.as_view()), name='auth-disable'),
    url(r'^edit/(?P<username>[\w.@+-]+)/$', lr(EditUserView.as_view()), name='auth-edit'),
    url(r'^delete/(?P<username>[\w.@+-]+)/$', lr(DeleteAuthView.as_view()), name='auth-delete'),
)
