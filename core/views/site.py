from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout as auth_logout
from django.db import models
from django.contrib.auth.forms import PasswordChangeForm

from core.models import User, Page
from core.views.forms import RegisteringForm, LoginForm, UserEditForm, PageEditForm, PagePropForm

import logging

logging.basicConfig(level=logging.DEBUG)

def index(request, context=None):
    if context == None:
        return render(request, "core/index.html", {'title': 'Bienvenue!'})
    else:
        return render(request, "core/index.html", context)

