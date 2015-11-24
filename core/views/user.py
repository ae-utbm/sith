# This file contains all the views that concern the user model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import PasswordChangeForm
import logging

from core.views.forms import RegisteringForm, LoginForm, UserEditForm
from core.models import User

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

def login(request):
    """
    The login view

    Needs to be improve with correct handling of form exceptions
    """
    context = {'title': 'Login'}
    if request.method == 'POST':
        try:
            form = LoginForm(request)
            form.login()
            context['tests'] = 'LOGIN_OK'
            return render(request, 'core/index.html', context)
        except Exception as e:
            logging.debug(e)
            context['error'] = "Login failed"
            context['tests'] = 'LOGIN_FAIL'
    else:
        form = LoginForm()
    context['form'] = form.as_p()
    return render(request, "core/login.html", context)

def logout(request):
    """
    The logout view
    """
    auth_logout(request)
    return redirect('core:index')

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
