# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, Http404

from django.views.generic.list import ListView

from .forms import UserCreationForm
from preup_ui.config.models import AppSettings
from preup_ui.utils.views import return_error

from django.views.generic import TemplateView, FormView, View
from django.contrib.auth.models import User
from django.shortcuts import redirect, get_object_or_404
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorList


class AuthListView(ListView):
    template_name = "auth/user_list.html"
    queryset = User.objects.all()

    def get_context_data(self, **kwargs):
        context = super(AuthListView, self).get_context_data(**kwargs)
        context['auth_enabled'] = not AppSettings.get_disable_auth()
        context['title'] = 'User List'
        return context


class GenericCreateUserView(FormView, TemplateView):
    """View for creating users"""
    # this View should not be rendered directly

    def post(self, request, *args, **kwargs):
        context = {}
        context['title'] = 'Create User'
        context['form'] = UserCreationForm(request.POST)
        if context['form'].is_valid():
            if User.objects.filter(username=context['form'].cleaned_data['username']).exists():
                errors = context['form']._errors.setdefault(NON_FIELD_ERRORS, ErrorList())
                errors.append(u"There is already a user with such username.")
                return self.render_to_response(context)
            User.objects.create_superuser(
                context['form'].cleaned_data['username'],
                context['form'].cleaned_data['email'],
                context['form'].cleaned_data['password']
            )

            try:
                return HttpResponseRedirect(request.GET['next'])
            except KeyError:
                pass
            return redirect('auth-list')
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        context = {}
        context['title'] = 'Create User'
        context.update(self.get_context_data(**kwargs))
        context['form'] = UserCreationForm()
        return self.render_to_response(context)


class FirstRunView(GenericCreateUserView):
    template_name = "auth/first_run.html"

    def get_context_data(self, **kwargs):
        context = super(FirstRunView, self).get_context_data(**kwargs)
        context['title'] = 'Welcome to Preupgrade Assistant UI'
        return context

    def post(self, request, *args, **kwargs):
        AppSettings.set_disable_auth(False)
        return super(FirstRunView, self).post(request, *args, **kwargs)


class CreateUserView(GenericCreateUserView):
    template_name = "auth/create_user.html"


class EditUserView(GenericCreateUserView):
    """View for editing users"""
    template_name = "auth/create_user.html"

    def get_context_data(self, **kwargs):
        context = super(EditUserView, self).get_context_data(**kwargs)
        context['edit'] = True
        try:
            context['title'] = "Edit User '%s'" % kwargs['username']
        except KeyError:
            raise Http404("There is no such user.")
        context['post_url_name'] = reverse("auth-edit", args=(kwargs['username'], ))
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = UserCreationForm(request.POST)
        if context['form'].is_valid():
            user = get_object_or_404(User, username=context['form'].cleaned_data['username'])
            user.password = context['form'].cleaned_data['password']
            user.email = context['form'].cleaned_data['email']
            user.save()
            return redirect('auth-list')
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        user = get_object_or_404(User, username=kwargs['username'])
        context['form'] = UserCreationForm(
            {'username': user.username, 'email': user.email},
            edit_mode=True,
        )
        context['next'] = 'index'
        return self.render_to_response(context)


class GenericAuthMngmntView(View):
    def get(self, request, *args, **kwargs):
        try:
            return HttpResponseRedirect(request.GET['next'])
        except KeyError:
            pass
        return redirect('results-list')


class DisableAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        AppSettings.set_disable_auth(True)
        AppSettings.set_disable_local_auth(True)
        return super(DisableAuthView, self).get(request, *args, **kwargs)


class EnableAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        if not User.objects.exists():
            return return_error(
                request,
                "There were no users created. If you enable authentication, \
you won't be able to log in. Please, create some user account first.")
        AppSettings.set_disable_auth(False)
        return super(EnableAuthView, self).get(request, *args, **kwargs)


class DisableLocalAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        AppSettings.set_disable_local_auth(True)
        return super(DisableLocalAuthView, self).get(request, *args, **kwargs)


class EnableLocalAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        if not User.objects.exists():
            return return_error(
                request,
                "There were no users created. If you enable authentication, \
you won't be able to log in. Please, create some user account first.")
        AppSettings.set_disable_local_auth(False)
        AppSettings.set_disable_auth(False)
        return super(EnableLocalAuthView, self).get(request, *args, **kwargs)


class DeleteAuthView(View):
    def get(self, request, username, *args, **kwargs):
        User.objects.filter(username=username).delete()
        return redirect('auth-list')
