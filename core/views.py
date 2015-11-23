from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout as auth_logout
from django.db import models

from .models import User, Page
from .forms import RegisteringForm, LoginForm, PageForm

import logging

logging.basicConfig(level=logging.DEBUG)

# This is a global default context that can be used everywhere and provide default basic values
# It needs to be completed by every function using templates
#context = {'title': 'Bienvenue!',
#           'tests': '',
#          }

def index(request, context=None):
    if context == None:
        return render(request, "core/index.html", {'title': 'Bienvenue!'})
    else:
        return render(request, "core/index.html", context)

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
    The logout view:w
    """
    auth_logout(request)
    return redirect('core:index')

def user(request, user_id=None):
    context = {'title': 'View a user'}
    if user_id == None:
        context['user_list'] = User.objects.all
        return render(request, "core/user.html", context)
    context['profile'] = get_object_or_404(User, pk=user_id)
    return render(request, "core/user.html", context)

def user_edit(request, user_id=None):
    user_id = int(user_id)
    context = {'title': 'Edit a user'}
    if user_id is not None:
        user_id = int(user_id)
        if request.user.is_authenticated() and (request.user.pk == user_id or request.user.is_superuser):
            context['profile'] = get_object_or_404(User, pk=user_id)
            return render(request, "core/edit_user.html", context)
    return user(request, user_id)

def page(request, page_name=None):
    context = {'title': 'View a Page'}
    if page_name == None:
        context['page_list'] = Page.objects.all
        return render(request, "core/page.html", context)
    context['page'] = Page.get_page_by_full_name(page_name)
    if context['page'] is not None:
        context['view_page'] = True
        context['title'] = context['page'].title
        context['test'] = "PAGE_FOUND"
    else:
        context['title'] = "This page does not exist"
        context['new_page'] = page_name
        context['test'] = "PAGE_NOT_FOUND"
    return render(request, "core/page.html", context)

def page_edit(request, page_name=None):
    context = {'title': 'Edit a page',
               'page_name': page_name}
    p = Page.get_page_by_full_name(page_name)
    if p == None:
        p = Page(name=page_name)
    if request.method == 'POST':
        f = PageForm(request.POST, instance=p)
        if f.is_valid():
            f.save()
            context['tests'] = "PAGE_SAVED"
        else:
            context['tests'] = "PAGE_NOT_SAVED"
    else:
        context['tests'] = "POST_NOT_RECEIVED"
        f = PageForm(instance=p)
    context['page'] = p
    context['page_form'] = f.as_p()
    return render(request, 'core/page.html', context)

