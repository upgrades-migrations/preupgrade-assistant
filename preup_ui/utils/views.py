# -*- coding: utf-8 -*-
"""
utils functions for rendering and displaying data
"""

import re

from django.http.response import Http404, HttpResponseForbidden
from django.template import RequestContext, loader


def return_error(request, message):
    context = RequestContext(request,
        {'message': message}
    )
    template = loader.get_template('error.html')
    return HttpResponseForbidden(template.render(context))


def state_filter_form_field_name(state, result_id):
    return state + str(result_id)

def is_state_filter(field_name):
    """
    is provided string a field in form for filtering by state?
    return state and result ID
    """
    m = re.match('(\w+?)(\d+)', field_name)
    if m:
        return m.groups()
    else:
        return None

def get_states_to_filter(get):
    if not get:
        return []
    states = []
    for key in get.keys():
        if get[key] == u'on':
            m = is_state_filter(key)
            if m is not None:
                states.append(m[0])
    return states
