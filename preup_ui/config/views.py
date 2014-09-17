# Create your views here.

from .forms import GenericStateFilterForm
from .models import AppSettings
from django.views.generic import FormView, TemplateView, RedirectView


class SettingsView(TemplateView):
    template_name = "config/settings.html"

    def get_context_data(self, **kwargs):

        current_state_setting = AppSettings.get_initial_state_filter()
        if current_state_setting:
            state_form = GenericStateFilterForm(initial={'state': current_state_setting})
        else:
            state_form = GenericStateFilterForm()
        context = {'state_form': state_form}
        return context

class SetStateSettingsView(FormView, RedirectView):

    def post(self, request, *args, **kwargs):
        gsff = GenericStateFilterForm(self.request.POST)

        if gsff.is_valid:
            states = gsff['state']

        AppSettings.set_initial_state_filter(states)


