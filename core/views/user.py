# This file contains all the views that concern the user model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, views
from django.core.urlresolvers import reverse
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, DetailView
import logging

from core.views.forms import RegisteringForm, UserGroupsForm
from core.models import User

def login(request):
    """
    The login view

    Needs to be improve with correct handling of form exceptions
    """
    return views.login(request, template_name="core/login.html")

def logout(request):
    """
    The logout view
    """
    return views.logout_then_login(request)

def password_change(request):
    """
    Allows a user to change its password
    """
    return views.password_change(request, template_name="core/password_change.html", post_change_redirect=reverse("core:password_change_done"))

def password_change_done(request):
    """
    Allows a user to change its password
    """
    return views.password_change_done(request, template_name="core/password_change_done.html")

def password_reset(request):
    """
    Allows someone to enter an email adresse for resetting password
    """
    return views.password_reset(request,
                                template_name="core/password_reset.html",
                                email_template_name="core/password_reset_email.html",
                                post_reset_redirect="core:password_reset_done",
                               )

def password_reset_done(request):
    """
    Confirm that the reset email has been sent
    """
    return views.password_reset_done(request, template_name="core/password_reset_done.html")

def password_reset_confirm(request, uidb64=None, token=None):
    """
    Provide a reset password formular
    """
    return views.password_reset_confirm(request, uidb64=uidb64, token=token,
                                        post_reset_redirect="core:password_reset_complete",
                                        template_name="core/password_reset_confirm.html",
                                       )

def password_reset_complete(request):
    """
    Confirm the password has sucessfully been reset
    """
    return views.password_reset_complete(request,
                                         template_name="core/password_reset_complete.html",
                                        )


def register(request):
    context = {'title': 'Register a user'}
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
    return render(request, "core/register.html", context)

class UserView(DetailView):
    """
    Display a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"

class UserListView(ListView):
    """
    Displays the user list
    """
    model = User

class UserUpdateProfileView(UpdateView):
    """
    Edit a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_edit.html"
    fields = ('first_name', 'last_name', 'nick_name', 'email', 'date_of_birth', )

class UserUpdateGroupsView(UpdateView):
    """
    Edit a user's groups
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_groups.html"
    form_class = UserGroupsForm

