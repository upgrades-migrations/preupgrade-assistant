# -*- coding: utf-8 -*-

from django.conf.urls import *

urlpatterns = patterns("",
    url(r"^submit/$", "preup_ui.xmlrpc_backend.views.submission_handler"),
)
