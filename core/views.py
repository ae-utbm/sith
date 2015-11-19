from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout as auth_logout

from .models import User
from .forms import RegisteringForm, LoginForm

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
    auth_logout(request)
    return redirect('core:index')

def user(request, user_id=None):
    if user_id == None:
        return render(request, "core/user.html", {'user_list': User.objects.all})
    user = get_object_or_404(User, pk=user_id)
    return render(request, "core/user.html", {'profile': user})

def user_edit(request, user_id):
    pass

