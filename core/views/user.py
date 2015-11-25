# This file contains all the views that concern the user model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, views
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse
import logging

from core.views.forms import RegisteringForm, LoginForm, UserEditForm
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
    return views.password_change(request, template_name="core/password_change.html")

def password_change_done(request):
    """
    Allows a user to change its password
    """
    return views.password_change_done(request, template_name="core/password_change_done.html")

def password_reset_confirm(request):
    pass

def password_reset_complete(request):
    pass

def password_reset_done(request):
    pass

def password_reset(request):
    pass

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

def user(request, user_id=None):
    """
    Display a user's profile
    """
    context = {'title': 'View a user'}
    if user_id == None:
        context['user_list'] = User.objects.all
        return render(request, "core/user.html", context)
    context['profile'] = get_object_or_404(User, pk=user_id)
    return render(request, "core/user.html", context)

def user_edit(request, user_id=None):
    """
    This view allows a user, or the allowed users to modify a profile
    """
    user_id = int(user_id)
    context = {'title': 'Edit a user'}
    if user_id is not None:
        user_id = int(user_id)
        if request.user.is_authenticated() and (request.user.pk == user_id or request.user.is_superuser):
            p = get_object_or_404(User, pk=user_id)
            if request.method == 'POST':
                f = UserEditForm(request.POST, instance=p)
                # Saving user
                if f.is_valid():
                    f.save()
                    context['tests'] = "USER_SAVED"
                else:
                    context['tests'] = "USER_NOT_SAVED"
            else:
                f = UserEditForm(instance=p)
            context['profile'] = p
            context['user_form'] = f.as_p()
            return render(request, "core/edit_user.html", context)
    return user(request, user_id)
