# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, TemplateView
from django.conf import settings

import json

from haystack.query import SearchQuerySet

from core.models import User, Notification
from core.utils import doku_to_markdown, bbcode_to_markdown
from club.models import Club


def index(request, context=None):
    if request.user.is_authenticated():
        from com.views import NewsListView

        return NewsListView.as_view()(request)
    return render(request, "core/index.jinja")


class NotificationList(ListView):
    model = Notification
    template_name = "core/notification_list.jinja"

    def get_queryset(self):
        if "see_all" in self.request.GET.keys():
            for n in self.request.user.notifications.all():
                n.viewed = True
                n.save()
        return self.request.user.notifications.order_by("-date")[:20]


def notification(request, notif_id):
    notif = Notification.objects.filter(id=notif_id).first()
    if notif:
        if notif.type not in settings.SITH_PERMANENT_NOTIFICATIONS:
            notif.viewed = True
        else:
            notif.callback()
        notif.save()
        return redirect(notif.url)
    return redirect("/")


def search_user(query, as_json=False):
    res = (
        SearchQuerySet()
        .models(User)
        .filter(text=query)
        .filter_or(text__contains=query)[:20]
    )
    return [r.object for r in res]


def search_club(query, as_json=False):
    clubs = []
    if query:
        clubs = Club.objects.filter(name__icontains=query).all()
        clubs = clubs[:5]
        if (
            as_json
        ):  # Re-loads json to avoid double encoding by JsonResponse, but still benefit from serializers
            clubs = json.loads(serializers.serialize("json", clubs, fields=("name")))
        else:
            clubs = list(clubs)
    return clubs


@login_required
def search_view(request):
    result = {
        "users": search_user(request.GET.get("query", "")),
        "clubs": search_club(request.GET.get("query", "")),
    }
    return render(request, "core/search.jinja", context={"result": result})


@login_required
def search_user_json(request):
    result = {"users": search_user(request.GET.get("query", ""), True)}
    return JsonResponse(result)


@login_required
def search_json(request):
    result = {
        "users": search_user(request.GET.get("query", ""), True),
        "clubs": search_club(request.GET.get("query", ""), True),
    }
    return JsonResponse(result)


class ToMarkdownView(TemplateView):
    template_name = "core/to_markdown.jinja"

    def post(self, request, *args, **kwargs):
        self.text = request.POST["text"]
        if request.POST["syntax"] == "doku":
            self.text_md = doku_to_markdown(self.text)
        else:
            self.text_md = bbcode_to_markdown(self.text)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        kwargs = super(ToMarkdownView, self).get_context_data(**kwargs)
        try:
            kwargs["text"] = self.text
            kwargs["text_md"] = self.text_md
        except:
            kwargs["text"] = ""
            kwargs["text_md"] = ""
        return kwargs
