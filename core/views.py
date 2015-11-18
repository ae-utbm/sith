from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout as auth_logout

from .models import User
from .forms import RegisteringForm, LoginForm

import logging

logging.basicConfig(level=logging.DEBUG)

def index(request):
    return HttpResponse("Hello, world. You're at the core index.")

def register(request):
    if request.method == 'POST':
        form = RegisteringForm(request.POST)
        if form.is_valid():
            logging.debug("Registering "+form.cleaned_data['first_name']+form.cleaned_data['last_name'])
            u = form.save()
            form = RegisteringForm()
    else:
        form = RegisteringForm()
    return render(request, "core/register.html", {'title': 'Register a user', 'form': form.as_p()})

def login(request):
    if request.method == 'POST':
        try:
            form = LoginForm(request)
            form.login()
            # TODO redirect to profile when done
            return redirect('index')
        except Exception as e:
            logging.debug(e)
    else:
        form = LoginForm()
    return render(request, "core/login.html", {'title': 'Login', 'form': form.as_p()})

def logout(request):
    auth_logout(request)
    return redirect('core:index')
