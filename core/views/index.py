#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
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
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from club.models import Club
from core.models import Notification, User
from core.schemas import UserFilterSchema


class NotificationList(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "core/notification_list.jinja"

    def get_queryset(self) -> QuerySet[Notification]:
        if "see_all" in self.request.GET:
            self.request.user.notifications.filter(viewed=False).update(viewed=True)
        return self.request.user.notifications.order_by("-date")[:20]


def notification(request: HttpRequest, notif_id: int):
    notif = get_object_or_404(Notification, id=notif_id)
    if notif.type not in settings.SITH_PERMANENT_NOTIFICATIONS:
        notif.viewed = True
    else:
        notif.callback()
    notif.save()
    return redirect(notif.url)


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "core/search.jinja"

    def get_context_data(self, **kwargs):
        users, clubs = [], []
        if query := self.request.GET.get("query"):
            users = list(
                UserFilterSchema(search=query)
                .filter(User.objects.viewable_by(self.request.user))
                .order_by(F("last_login").desc(nulls_last=True))
            )
            clubs = list(Club.objects.filter(name__icontains=query)[:5])
        return super().get_context_data(**kwargs) | {"users": users, "clubs": clubs}
