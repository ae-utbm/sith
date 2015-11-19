from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout as auth_logout

from .models import User
from .forms import RegisteringForm, LoginForm

import logging

logging.basicConfig(level=logging.DEBUG)

def index(request):
    return render(request, "core/index.html", {'title': 'Bienvenue!'})

def register(request):
    context = {'title': 'Register a user'}
    if request.method == 'POST':
        form = RegisteringForm(request.POST)
        if form.is_valid():
            logging.debug("Registering "+form.cleaned_data['first_name']+form.cleaned_data['last_name'])
            u = form.save()
            context['user_registered'] = u
            form = RegisteringForm()
    else:
        form = RegisteringForm()
    context['form'] = form.as_p()
    return render(request, "core/register.html", context)

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

def user(request, user_id=None):
    if user_id == None:
        return render(request, "core/user.html", {'user_list': User.objects.all})
    user = get_object_or_404(User, pk=user_id)
    return render(request, "core/user.html", {'profile': user})

def user_edit(request, user_id):
    pass

