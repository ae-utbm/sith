from django.shortcuts import render
from django.http import HttpResponse

from .models import User
from .forms import RegisteringForm

import logging

logging.basicConfig(level=logging.DEBUG)

def index(request):
    return HttpResponse("Hello, world. You're at the core index.")

def login(request):
    return HttpResponse("Login page")

def register(request):
    if request.method == 'POST':
        logging.debug("Registering "+request.POST['username'])
        form = RegisteringForm(request.POST)
        if form.is_valid():
            u = User(username=request.POST['username'], password=request.POST['password1'], email="guy@plop.guy")
            u.save()
            return render(request, "sith/register.html", {'username': u.get_username(),
                                                          'form': RegisteringForm().as_ul()})
        else:
            return render(request, "sith/register.html", {'form': form.as_ul()})
    form = RegisteringForm()
    return render(request, "sith/register.html", {'form': form.as_ul()})

def guy(request):
    return HttpResponse("Guyuguyguygé")
