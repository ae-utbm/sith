# This file contains all the views that concern the user model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, views
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, DetailView, TemplateView
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.conf import settings
import logging

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin
from core.views.forms import RegisteringForm, UserPropForm, UserProfileForm
from core.models import User

def login(request):
    """
    The login view

    Needs to be improve with correct handling of form exceptions
    """
    return views.login(request, template_name="core/login.jinja")

def logout(request):
    """
    The logout view
    """
    return views.logout_then_login(request)

def password_change(request):
    """
    Allows a user to change its password
    """
    return views.password_change(request, template_name="core/password_change.jinja", post_change_redirect=reverse("core:password_change_done"))

def password_change_done(request):
    """
    Allows a user to change its password
    """
    return views.password_change_done(request, template_name="core/password_change_done.jinja")

def password_reset(request):
    """
    Allows someone to enter an email adresse for resetting password
    """
    return views.password_reset(request,
                                template_name="core/password_reset.jinja",
                                email_template_name="core/password_reset_email.jinja",
                                post_reset_redirect="core:password_reset_done",
                               )

def password_reset_done(request):
    """
    Confirm that the reset email has been sent
    """
    return views.password_reset_done(request, template_name="core/password_reset_done.jinja")

def password_reset_confirm(request, uidb64=None, token=None):
    """
    Provide a reset password formular
    """
    return views.password_reset_confirm(request, uidb64=uidb64, token=token,
                                        post_reset_redirect="core:password_reset_complete",
                                        template_name="core/password_reset_confirm.jinja",
                                       )

def password_reset_complete(request):
    """
    Confirm the password has sucessfully been reset
    """
    return views.password_reset_complete(request,
                                         template_name="core/password_reset_complete.jinja",
                                        )


def register(request):
    context = {}
    if request.method == 'POST':
        form = RegisteringForm(request.POST)
        if form.is_valid():
            logging.debug("Registering "+form.cleaned_data['first_name']+form.cleaned_data['last_name'])
            u = form.save()
            context['user_registered'] = u
            context['tests'] = 'TEST_REGISTER_USER_FORM_OK'
            form = RegisteringForm()
        else:
            context['error'] = 'Erreur'
            context['tests'] = 'TEST_REGISTER_USER_FORM_FAIL'
    else:
        form = RegisteringForm()
    context['form'] = form.as_p()
    return render(request, "core/register.jinja", context)

class UserView(CanViewMixin, DetailView):
    """
    Display a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_detail.jinja"

class UserListView(ListView):
    """
    Displays the user list
    """
    model = User
    template_name = "core/user_list.jinja"

class UserUpdateProfileView(CanEditMixin, UpdateView):
    """
    Edit a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_edit.jinja"
    form_class = UserProfileForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if self.form.instance.profile_pict and not request.user.is_in_group(settings.SITH_MAIN_BOARD_GROUP):
            self.form.fields.pop('profile_pict', None)
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if self.form.instance.profile_pict and not request.user.is_in_group(settings.SITH_MAIN_BOARD_GROUP):
            self.form.fields.pop('profile_pict', None)
        files = request.FILES.items()
        self.form.process(files)
        if request.user.is_authenticated() and request.user.can_edit(self.object) and self.form.is_valid():
            return super(UserUpdateProfileView, self).form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(UserUpdateProfileView, self).get_context_data(**kwargs)
        kwargs['profile'] = self.form.instance
        kwargs['form'] = self.form
        return kwargs

class UserUpdateGroupView(CanEditPropMixin, UpdateView):
    """
    Edit a user's groups
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_group.jinja"
    form_class = modelform_factory(User, fields=['groups'],
            widgets={'groups':CheckboxSelectMultiple})
    context_object_name = "profile"

class UserToolsView(TemplateView):
    """
    Displays the logged user's tools
    """
    template_name = "core/user_tools.jinja"

    def get_context_data(self, **kwargs):
        from launderette.models import Launderette
        kwargs = super(UserToolsView, self).get_context_data(**kwargs)
        kwargs['launderettes'] = Launderette.objects.all()
        return kwargs

class UserAccountView(DetailView):
    """
    Display a user's account
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_account.jinja"

    def dispatch(self, request, *arg, **kwargs): # Manually validates the rights
        res = super(UserAccountView, self).dispatch(request, *arg, **kwargs)
        if (self.object == request.user
                or request.user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name'])
                or request.user.is_in_group(settings.SITH_GROUPS['root']['name'])):
            return res
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        kwargs = super(UserAccountView, self).get_context_data(**kwargs)
        kwargs['profile'] = self.object
        try:
            kwargs['customer'] = self.object.customer
        except:
            pass
        # TODO: add list of month where account has activity
        return kwargs


