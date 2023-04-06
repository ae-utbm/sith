# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import html
from django.utils.text import slugify
from django.views.generic import ListView, TemplateView
from haystack.query import SearchQuerySet

from club.models import Club
from core.models import Notification, User
from core.utils import bbcode_to_markdown, doku_to_markdown


def index(request, context=None):
    from com.views import NewsListView

    return NewsListView.as_view()(request)


class NotificationList(ListView):
    model = Notification
    template_name = "core/notification_list.jinja"

    def get_queryset(self) -> QuerySet[Notification]:
        if self.request.user.is_anonymous:
            return Notification.objects.none()
        # TODO: Bulk update in django 2.2
        if "see_all" in self.request.GET.keys():
            for n in self.request.user.notifications.filter(viewed=False):
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
    try:
        # slugify turns everything into ascii and every whitespace into -
        # it ends by removing duplicate - (so ' - ' will turn into '-')
        # replace('-', ' ') because search is whitespace based
        query = slugify(query).replace("-", " ")
        # TODO: is this necessary?
        query = html.escape(query)
        res = (
            SearchQuerySet()
            .models(User)
            .autocomplete(auto=query)
            .order_by("-last_update")[:20]
        )
        return [r.object for r in res]
    except TypeError:
        return []


def search_club(query, as_json=False):
    clubs = []
    if query:
        clubs = Club.objects.filter(name__icontains=query).all()
        clubs = clubs[:5]
        if as_json:
            # Re-loads json to avoid double encoding by JsonResponse, but still benefit from serializers
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
