from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import models

import logging

logging.basicConfig(level=logging.DEBUG)

def index(request, context=None):
    if context == None:
        return render(request, "core/index.html", {'title': 'Bienvenue!'})
    else:
        return render(request, "core/index.html", context)

