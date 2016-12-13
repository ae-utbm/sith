from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.http import JsonResponse
from django.core import serializers
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView

import os
import json
from itertools import chain

from core.models import User, Notification
from club.models import Club

def index(request, context=None):
    return render(request, "core/index.jinja")

class NotificationList(ListView):
    model = Notification
    template_name = "core/notification_list.jinja"

    def get_queryset(self):
        if 'see_all' in self.request.GET.keys():
            self.request.user.notifications.update(viewed=True)
        return self.request.user.notifications.order_by('-id')[:20]

def notification(request, notif_id):
    notif = Notification.objects.filter(id=notif_id).first()
    if notif:
        notif.viewed = True
        notif.save()
        return redirect(notif.url)
    return redirect("/")

def search_user(query, as_json=False):
    users = []
    if query:
        exact_nick = User.objects.filter(nick_name__iexact=query).all()
        nicks = User.objects.filter(nick_name__icontains=query).exclude(id__in=exact_nick).all()
        users = User.objects.filter(Q(first_name__icontains=query) |
                Q(last_name__icontains=query)).exclude(id__in=exact_nick).exclude(id__in=nicks).all()
        nicks = nicks[:5]
        users = users[:50]
        if as_json: # Re-loads json to avoid double encoding by JsonResponse, but still benefit from serializers
            exact_nick = json.loads(serializers.serialize('json', exact_nick, fields=('nick_name', 'last_name', 'first_name', 'profile_pict')))
            nicks = json.loads(serializers.serialize('json', nicks, fields=('nick_name', 'last_name', 'first_name', 'profile_pict')))
            users = json.loads(serializers.serialize('json', users, fields=('nick_name', 'last_name', 'first_name', 'profile_pict')))
        else:
            exact_nick = list(exact_nick)
            nicks = list(nicks)
            users = list(users)
        users = exact_nick + nicks + users
    return users

def search_club(query, as_json=False):
    clubs = []
    if query:
        clubs = Club.objects.filter(name__icontains=query).all()
        clubs = clubs[:5]
        if as_json: # Re-loads json to avoid double encoding by JsonResponse, but still benefit from serializers
            clubs = json.loads(serializers.serialize('json', clubs, fields=('name')))
        else:
            clubs = list(clubs)
    return clubs

@login_required
def search_view(request):
    result = {
            'users': search_user(request.GET.get('query', '')),
            'clubs': search_club(request.GET.get('query', '')),
            }
    return render(request, "core/search.jinja", context={'result': result})

@login_required
def search_user_json(request):
    result = {
            'users': search_user(request.GET.get('query', ''), True),
            }
    return JsonResponse(result)

@login_required
def search_json(request):
    result = {
            'users': search_user(request.GET.get('query', ''), True),
            'clubs': search_club(request.GET.get('query', ''), True),
            }
    return JsonResponse(result)

