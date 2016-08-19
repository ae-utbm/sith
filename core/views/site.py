from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.http import JsonResponse
from django.core import serializers
from django.db.models import Q
from django.contrib.auth.decorators import login_required

import os
import json
from itertools import chain

from core.models import User
from club.models import Club

def index(request, context=None):
    return render(request, "core/index.jinja")

def search(query, as_json=False):
    result = {'users': None, 'clubs': None}
    if query:
        nicks = User.objects.filter(nick_name__icontains=query).all()
        users = User.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query)).all()
        clubs = Club.objects.filter(name__icontains=query).all()
        nicks = nicks[:5]
        users = users[:5]
        clubs = clubs[:5]
        if as_json: # Re-loads json to avoid double encoding by JsonResponse, but still benefit from serializers
            nicks = json.loads(serializers.serialize('json', nicks, fields=('nick_name', 'last_name', 'first_name', 'profile_pict')))
            users = json.loads(serializers.serialize('json', users, fields=('nick_name', 'last_name', 'first_name', 'profile_pict')))
            clubs = json.loads(serializers.serialize('json', clubs, fields=('name')))
        else:
            nicks = list(nicks.all())
            users = list(users.all())
            clubs = list(clubs.all())
        result['users'] = nicks + users
        result['clubs'] = clubs
    return result

@login_required
def search_view(request):
    return render(request, "core/search.jinja", context={'result': search(request.GET.get('query', ''))})

@login_required
def search_json(request):
    return JsonResponse(search(request.GET.get('query', ''), True))

