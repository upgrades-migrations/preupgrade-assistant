from preupg.ui.config.models import AppSettings
from preupg.ui.report.forms import StateFilterForm

from django import template
from preupg.ui.utils.views import get_states_to_filter

register = template.Library()


@register.filter(name='state_filter_form')
def state_filter_form(result, get=None):
    states = get_states_to_filter(get)
    if states:
        form = StateFilterForm(get, result=result)
    else:
        init_states = AppSettings.get_initial_state_filter()
        inital_conf = {}
        for i in init_states:
            key = i + str(result.id)
            inital_conf[key] = True
        form = StateFilterForm(result=result, initial=inital_conf)
    return form
state_filter_form.is_safe = True
