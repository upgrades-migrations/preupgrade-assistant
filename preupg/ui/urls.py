from django import VERSION
from django.conf.urls import patterns, include, url
from django.contrib import admin
from preupg.ui.auth.views import FirstRunView, FirstRunDisableAuthView, login, logout
from preupg.ui.auth.decorators import first_run_required as frr

if VERSION < (1, 7):
    admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('preupg.ui.report.urls')),

    #url(r'^settings/', include('preupg.ui.config.urls')),

    url(r"^xmlrpc/", include("preupg.ui.xmlrpc_backend.urls"), name="xmlrpc"),

    # shortcut for XML-RPC submission
    url(r"^submit/$", "preupg.ui.xmlrpc_backend.views.submission_handler", name="xmlrpc-submit"),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^compare/', include('preupg.ui.compare.urls')),

    # private auth URLs
    url(r'^auth/', include('preupg.ui.auth.urls')),

    # public auth URLs -- first display and login itself
    url(r'^login/$', login, {'template_name': 'auth/login.html'}, name='auth-login'),
    url(r'^logout/$', logout, {'template_name': 'auth/logout.html'}, name='auth-logout'),
    url(r'^first/$', frr(FirstRunView.as_view()), name='first-run'),
    url(r'^first/disable/$', frr(FirstRunDisableAuthView.as_view()), name='first-run-disable-auth'),
)
