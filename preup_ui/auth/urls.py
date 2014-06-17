# -*- coding: utf-8 -*-

from auth.views import *

from django.conf.urls import patterns, url

# these are private URLs for auth management

urlpatterns = patterns('',
    url(r'^list/$', AuthListView.as_view(), name='auth-list'),
    url(r'^create/$', CreateUserView.as_view(), name='auth-create'),
    url(r'^disable/$', DisableAuthView.as_view(), name='auth-disable'),
    url(r'^enable/$', EnableAuthView.as_view(), name='auth-enable'),
    url(r'^disable-local/$', DisableLocalAuthView.as_view(), name='local-auth-disable'),
    url(r'^enable-local/$', EnableLocalAuthView.as_view(), name='local-auth-enable'),
    url(r'^edit/(?P<username>[\w.@+-]+)/$', EditUserView.as_view(), name='auth-edit'),
    url(r'^delete/(?P<username>[\w.@+-]+)/$', DeleteAuthView.as_view(), name='auth-delete'),
)