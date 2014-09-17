# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import redirect
from re import compile
from preup_ui.config.models import AppSettings

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

class CustomAuthMiddleware(object):
    """
    Middleware that requires a user to be authenticated if application is
    served over network.

    Also contains hook for displaying special screen when app is launched first time.

    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """
    def process_request(self, request):
        assert hasattr(request, 'user'), "The RequireAuthOnPublicMiddleware middleware\
 requires authentication middleware to be installed. Edit your\
 MIDDLEWARE_CLASSES setting to insert\
 'django.contrib.auth.middlware.AuthenticationMiddleware'. If that doesn't\
 work, ensure your TEMPLATE_CONTEXT_PROCESSORS setting includes\
 'django.core.context_processors.auth'."

        disable_auth = AppSettings.get_disable_auth()

        if disable_auth is None:
            # running first time
            if not any(request.path_info.lstrip('/').startswith(x)
                       for x in ['admin/', 'first/']):
                # lets dont stuck in infinite redirect loop
                return redirect('first-run')

        clients_addr = request.META['REMOTE_ADDR']

        if disable_auth is not None and disable_auth is False:
            # auth is enabled
            if clients_addr not in ['127.0.0.1', 'localhost', '::1']:
                # network access
                if request.user.is_authenticated():
                    return
            else:
                # local access
                disable_local_auth = AppSettings.get_disable_local_auth()
                if disable_local_auth or request.user.is_authenticated():
                    return
            # at this point, we know that app is served over network
            # and user is not authenticated
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)
