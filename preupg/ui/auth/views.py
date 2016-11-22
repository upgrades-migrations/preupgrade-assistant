# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect, Http404
from django.utils.http import is_safe_url

from django.views.generic.list import ListView

from .forms import UserCreationForm
from preupg.ui.config.models import AppSettings
from preupg.ui.utils.views import return_error

from django.views.generic import TemplateView, DeleteView, FormView, View
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login as auth_login, get_user_model
from django.contrib.auth.views import login as auth_login_view, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, resolve_url, get_object_or_404
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorList


def login(request, **kwargs):
    if get_user_model().objects.count() == 0:
        return redirect('first-run')
    else:
        # tries to authenticate without credentials (with AutologinBackend)
        u = authenticate()
        if u is not None:
            auth_login(request, u)
            redirect_to = request.REQUEST.get(kwargs.get('redirect_field_name', REDIRECT_FIELD_NAME), '')
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
            return HttpResponseRedirect(redirect_to)
        else:
            return auth_login_view(request, **kwargs)


class AuthListView(ListView):
    template_name = "auth/user_list.html"
    queryset = User.objects.all()

    def get_context_data(self, **kwargs):
        context = super(AuthListView, self).get_context_data(**kwargs)
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
        AppSettings.unset_autologin_user_id()
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
    def get_redirect(self):
        try:
            return HttpResponseRedirect(self.request.GET['next'])
        except KeyError:
            pass
        return redirect('results-list')


class FirstRunDisableAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        user = get_user_model()(username='autologin')
        user.save()
        AppSettings.set_autologin_user_id(user.id)
        return self.get_redirect()


class EnableAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        AppSettings.unset_autologin_user_id()
        return self.get_redirect()


class DisableAuthView(GenericAuthMngmntView):
    def get(self, request, *args, **kwargs):
        AppSettings.set_autologin_user_id(request.user.id)
        return self.get_redirect()


class DeleteAuthView(DeleteView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    success_url = reverse_lazy('auth-list')

