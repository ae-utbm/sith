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
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
import itertools
from datetime import date, timedelta
from smtplib import SMTPRecipientsRefused
from typing import Any

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
)
from django.contrib.syndication.views import Feed
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import localdate, now
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from club.models import Club, Mailing
from com.forms import NewsDateForm, NewsForm, PosterForm
from com.ics_calendar import IcsCalendar
from com.models import News, NewsDate, Poster, Screen, Sith, Weekmail, WeekmailArticle
from core.auth.mixins import (
    CanEditPropMixin,
    CanViewMixin,
    PermissionOrAuthorRequiredMixin,
    PermissionOrClubBoardRequiredMixin,
)
from core.models import User
from core.views.mixins import TabedViewMixin
from core.views.widgets.markdown import MarkdownInput

# Sith object

sith = Sith.objects.first


class ComTabsMixin(TabedViewMixin):
    tabs_title = _("Communication administration")

    def get_list_of_tabs(self):
        return [
            {"url": reverse("com:weekmail"), "slug": "weekmail", "name": _("Weekmail")},
            {
                "url": reverse("com:weekmail_destinations"),
                "slug": "weekmail_destinations",
                "name": _("Weekmail destinations"),
            },
            {
                "url": reverse("com:info_edit"),
                "slug": "info",
                "name": _("Info message"),
            },
            {
                "url": reverse("com:alert_edit"),
                "slug": "alert",
                "name": _("Alert message"),
            },
            {
                "url": reverse("com:mailing_admin"),
                "slug": "mailings",
                "name": _("Mailing lists administration"),
            },
            {
                "url": reverse("com:poster_list"),
                "slug": "posters",
                "name": _("Posters list"),
            },
            {
                "url": reverse("com:screen_list"),
                "slug": "screens",
                "name": _("Screens list"),
            },
        ]


class ComEditView(ComTabsMixin, CanEditPropMixin, UpdateView):
    model = Sith
    template_name = "core/edit.jinja"

    def get_object(self, queryset=None):
        return Sith.objects.first()


class AlertMsgEditView(ComEditView):
    form_class = modelform_factory(
        Sith, fields=["alert_msg"], widgets={"alert_msg": MarkdownInput}
    )
    current_tab = "alert"
    success_url = reverse_lazy("com:alert_edit")


class InfoMsgEditView(ComEditView):
    form_class = modelform_factory(
        Sith, fields=["info_msg"], widgets={"info_msg": MarkdownInput}
    )
    current_tab = "info"
    success_url = reverse_lazy("com:info_edit")


class WeekmailDestinationEditView(ComEditView):
    fields = ["weekmail_destinations"]
    current_tab = "weekmail_destinations"
    success_url = reverse_lazy("com:weekmail_destinations")


# News


class NewsCreateView(PermissionRequiredMixin, CreateView):
    """View to either create or update News."""

    model = News
    form_class = NewsForm
    template_name = "com/news_edit.jinja"
    permission_required = "com.add_news"

    def get_date_form_kwargs(self) -> dict[str, Any]:
        """Get initial data for NewsDateForm"""
        if self.request.method == "POST":
            return {"data": self.request.POST}
        return {}

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "author": self.request.user,
            "date_form": NewsDateForm(**self.get_date_form_kwargs()),
        }

    def get_initial(self):
        init = super().get_initial()
        # if the id of a club is provided, select it by default
        if club_id := self.request.GET.get("club"):
            init["club"] = Club.objects.filter(id=club_id).first()
        return init


class NewsUpdateView(PermissionOrAuthorRequiredMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = "com/news_edit.jinja"
    pk_url_kwarg = "news_id"
    permission_required = "com.edit_news"

    def form_valid(self, form):
        response = super().form_valid(form)  # Does the saving part
        IcsCalendar.make_internal()
        return response

    def get_date_form_kwargs(self) -> dict[str, Any]:
        """Get initial data for NewsDateForm"""
        response = {}
        if self.request.method == "POST":
            response["data"] = self.request.POST
        dates = list(self.object.dates.order_by("id"))
        if len(dates) == 0:
            return {}
        response["instance"] = dates[0]
        occurrences = NewsDateForm.get_occurrences(len(dates))
        if occurrences is not None:
            response["initial"] = {"is_weekly": True, "occurrences": occurrences}
        return response

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "author": self.request.user,
            "date_form": NewsDateForm(**self.get_date_form_kwargs()),
        }


class NewsDeleteView(PermissionOrAuthorRequiredMixin, DeleteView):
    model = News
    pk_url_kwarg = "news_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("com:news_admin_list")
    permission_required = "com.delete_news"


class NewsModerateView(PermissionRequiredMixin, DetailView):
    model = News
    pk_url_kwarg = "news_id"
    permission_required = "com.moderate_news"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "remove" in request.GET:
            self.object.is_published = False
        else:
            self.object.is_published = True
        self.object.moderator = request.user
        self.object.save()
        if "next" in self.request.GET:
            return redirect(self.request.GET["next"])
        return redirect("com:news_admin_list")


class NewsAdminListView(PermissionRequiredMixin, ListView):
    model = News
    template_name = "com/news_admin_list.jinja"
    queryset = News.objects.select_related(
        "club", "author", "moderator"
    ).prefetch_related("dates")
    permission_required = ["com.moderate_news", "com.delete_news"]


class NewsListView(TemplateView):
    template_name = "com/news_list.jinja"

    def get_birthdays(self):
        if not self.request.user.has_perm("core.view_user"):
            return []
        return itertools.groupby(
            User.objects.filter(
                date_of_birth__month=localdate().month,
                date_of_birth__day=localdate().day,
                is_subscriber_viewable=True,
            )
            .filter(role__in=["STUDENT", "FORMER STUDENT"])
            .order_by("-date_of_birth"),
            key=lambda u: u.date_of_birth.year,
        )

    def get_last_day(self) -> date | None:
        """Get the last day when news will be displayed

        The returned day is the third one where something happen.
        For example, if there are 6 events : A on 15/03, B and C on 17/03,
        D on 20/03, E on 21/03 and F on 22/03 ;
        then the result is 20/03.
        """
        dates = list(
            NewsDate.objects.filter(end_date__gt=now())
            .order_by("start_date")
            .values_list("start_date__date", flat=True)
            .distinct()[:4]
        )
        return dates[-1] if len(dates) > 0 else None

    def get_news_dates(self, until: date) -> dict[date, list[date]]:
        """Return the event dates to display.

        The selected events are the ones that happens between
        right now and the given day (included).
        """
        return {
            date: list(dates)
            for date, dates in itertools.groupby(
                NewsDate.objects.viewable_by(self.request.user)
                .filter(end_date__gt=now(), start_date__date__lte=until)
                .order_by("start_date")
                .select_related("news", "news__club"),
                key=lambda d: d.start_date.date(),
            )
        }

    def get_context_data(self, **kwargs):
        last_day = self.get_last_day()
        return super().get_context_data(**kwargs) | {
            "news_dates": self.get_news_dates(until=last_day)
            if last_day is not None
            else {},
            "birthdays": self.get_birthdays(),
            "last_day": last_day,
        }


class NewsDetailView(CanViewMixin, DetailView):
    model = News
    template_name = "com/news_detail.jinja"
    pk_url_kwarg = "news_id"
    queryset = News.objects.select_related("club", "author", "moderator")

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"date": self.object.dates.first()}


class NewsFeed(Feed):
    title = _("News")
    link = reverse_lazy("com:news_list")
    description = _("All incoming events")

    def items(self):
        return (
            NewsDate.objects.filter(
                news__is_published=True,
                end_date__gte=timezone.now() - (relativedelta(months=6)),
            )
            .select_related("news", "news__author")
            .order_by("-start_date")
        )

    def item_title(self, item: NewsDate):
        return item.news.title

    def item_description(self, item: NewsDate):
        return item.news.summary

    def item_link(self, item: NewsDate):
        return item.news.get_absolute_url()

    def item_author_name(self, item: NewsDate):
        return item.news.author.get_display_name()


# Weekmail


class WeekmailPreviewView(ComTabsMixin, CanEditPropMixin, DetailView):
    model = Weekmail
    template_name = "com/weekmail_preview.jinja"
    success_url = reverse_lazy("com:weekmail")
    current_tab = "weekmail"

    def dispatch(self, request, *args, **kwargs):
        self.bad_recipients = []
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(self.request, _("Weekmail sent successfully"))
        if request.POST["send"] == "validate":
            try:
                self.object.send()
                return HttpResponseRedirect(reverse("com:weekmail"))
            except SMTPRecipientsRefused as e:
                self.bad_recipients = e.recipients
        elif request.POST["send"] == "clean":
            try:
                self.object.send()  # This should fail
            except SMTPRecipientsRefused as e:
                users = User.objects.filter(email__in=e.recipients)
                for u in users:
                    u.preferences.receive_weekmail = False
                    u.preferences.save()
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.model.objects.filter(sent=False).order_by("-id").first()

    def get_context_data(self, **kwargs):
        """Add rendered weekmail."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["weekmail_rendered"] = self.object.render_html()
        kwargs["bad_recipients"] = self.bad_recipients
        return kwargs


class WeekmailEditView(ComTabsMixin, CanEditPropMixin, UpdateView):
    model = Weekmail
    template_name = "com/weekmail.jinja"
    form_class = modelform_factory(
        Weekmail,
        fields=["title", "intro", "joke", "protip", "conclusion"],
        help_texts={"title": _("Delete and save to regenerate")},
        widgets={
            "intro": MarkdownInput,
            "joke": MarkdownInput,
            "protip": MarkdownInput,
            "conclusion": MarkdownInput,
        },
    )
    success_url = reverse_lazy("com:weekmail")
    current_tab = "weekmail"

    def get_object(self, queryset=None):
        weekmail = self.model.objects.filter(sent=False).order_by("-id").first()
        if not weekmail.title:
            now = timezone.now()
            weekmail.title = _("Weekmail of the ") + (
                now + timedelta(days=6 - now.weekday())
            ).strftime("%d/%m/%Y")
            weekmail.save()
        return weekmail

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "up_article" in request.GET:
            art = get_object_or_404(
                WeekmailArticle, id=request.GET["up_article"], weekmail=self.object
            )
            prev_art = (
                self.object.articles.order_by("rank").filter(rank__lt=art.rank).last()
            )
            if prev_art:
                art.rank, prev_art.rank = prev_art.rank, art.rank
                art.save()
                prev_art.save()
                messages.success(
                    self.request,
                    _("%(title)s moved up in the Weekmail") % {"title": art.title},
                )
        if "down_article" in request.GET:
            art = get_object_or_404(
                WeekmailArticle, id=request.GET["down_article"], weekmail=self.object
            )
            next_art = (
                self.object.articles.order_by("rank").filter(rank__gt=art.rank).first()
            )
            if next_art:
                art.rank, next_art.rank = next_art.rank, art.rank
                art.save()
                next_art.save()
                messages.success(
                    self.request,
                    _("%(title)s moved down in the Weekmail") % {"title": art.title},
                )
        if "add_article" in request.GET:
            art = get_object_or_404(
                WeekmailArticle, id=request.GET["add_article"], weekmail=None
            )
            art.weekmail = self.object
            art.rank = self.object.articles.aggregate(Max("rank"))["rank__max"] or 0
            art.rank += 1
            art.save()
            messages.success(
                self.request,
                _("%(title)s added to the Weekmail") % {"title": art.title},
            )
        if "del_article" in request.GET:
            art = get_object_or_404(
                WeekmailArticle, id=request.GET["del_article"], weekmail=self.object
            )
            art.weekmail = None
            art.rank = -1
            art.save()
            messages.success(
                self.request,
                _("%(title)s removed from the Weekmail") % {"title": art.title},
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add orphan articles."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["orphans"] = WeekmailArticle.objects.filter(weekmail=None)
        return kwargs


class WeekmailArticleEditView(ComTabsMixin, CanEditPropMixin, UpdateView):
    """Edit an article."""

    model = WeekmailArticle
    form_class = modelform_factory(
        WeekmailArticle,
        fields=["title", "club", "content"],
        widgets={"content": MarkdownInput},
    )
    pk_url_kwarg = "article_id"
    template_name = "core/edit.jinja"
    success_url = reverse_lazy("com:weekmail")
    current_tab = "weekmail"


class WeekmailArticleCreateView(CreateView):
    """Post an article."""

    model = WeekmailArticle
    form_class = modelform_factory(
        WeekmailArticle,
        fields=["title", "club", "content"],
        widgets={"content": MarkdownInput},
    )
    template_name = "core/create.jinja"
    success_url = reverse_lazy("core:user_tools")

    def get_initial(self):
        if "club" not in self.request.GET:
            return {}
        return {"club": Club.objects.filter(id=self.request.GET.get("club")).first()}

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = form.instance
        form.is_valid()  # Valid a first time to populate club field
        m = form.instance.club.get_membership_for(request.user)
        if m is None or m.role <= settings.SITH_MAXIMUM_FREE_ROLE:
            form.add_error(
                "club",
                ValidationError(
                    _(
                        "You must be a board member of the selected club to post in the Weekmail."
                    )
                ),
            )
        if form.is_valid() and "preview" not in request.POST:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class WeekmailArticleDeleteView(CanEditPropMixin, DeleteView):
    """Delete an article."""

    model = WeekmailArticle
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("com:weekmail")
    pk_url_kwarg = "article_id"


class MailingListAdminView(ComTabsMixin, ListView):
    template_name = "com/mailing_admin.jinja"
    model = Mailing
    current_tab = "mailings"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_com_admin or request.user.is_root):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["moderated"] = self.get_queryset().filter(is_moderated=True).all()
        kwargs["unmoderated"] = self.get_queryset().filter(is_moderated=False).all()
        kwargs["has_moderated"] = len(kwargs["moderated"]) > 0
        kwargs["has_unmoderated"] = len(kwargs["unmoderated"]) > 0
        return kwargs


class MailingModerateView(View):
    def get(self, request, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=kwargs["mailing_id"])
        if mailing.can_moderate(request.user):
            mailing.is_moderated = True
            mailing.moderator = request.user
            mailing.save()
            return redirect("com:mailing_admin")

        raise PermissionDenied


class PosterListBaseView(PermissionOrClubBoardRequiredMixin, ListView):
    """List communication posters."""

    model = Poster
    template_name = "com/poster_list.jinja"
    permission_required = "com.view_poster"
    ordering = ["-date_begin"]

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"club": self.club}


class PosterCreateBaseView(PermissionOrClubBoardRequiredMixin, CreateView):
    """Create communication poster."""

    form_class = PosterForm
    template_name = "core/create.jinja"
    permission_required = "com.add_poster"

    def get_queryset(self):
        return Poster.objects.all()

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"user": self.request.user}

    def get_initial(self):
        return {"club": self.club}

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"club": self.club}

    def form_valid(self, form):
        if self.request.user.has_perm("com.moderate_poster"):
            form.instance.is_moderated = True
        return super().form_valid(form)


class PosterEditBaseView(PermissionOrClubBoardRequiredMixin, UpdateView):
    """Edit communication poster."""

    pk_url_kwarg = "poster_id"
    form_class = PosterForm
    template_name = "com/poster_edit.jinja"
    permission_required = "com.change_poster"

    def get_queryset(self):
        return Poster.objects.all()

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"user": self.request.user}

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"club": self.club}

    def form_valid(self, form):
        if not self.request.user.has_perm("com.moderate_poster"):
            form.instance.is_moderated = False
        return super().form_valid(form)


class PosterDeleteBaseView(
    PermissionOrClubBoardRequiredMixin, ComTabsMixin, DeleteView
):
    """Edit communication poster."""

    pk_url_kwarg = "poster_id"
    current_tab = "posters"
    model = Poster
    template_name = "core/delete_confirm.jinja"
    permission_required = "com.delete_poster"


class PosterListView(ComTabsMixin, PosterListBaseView):
    """List communication posters."""

    current_tab = "posters"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.has_perm("com.view_poster"):
            return qs
        return qs.filter(club=self.club.id)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["app"] = "com"
        return kwargs


class PosterCreateView(ComTabsMixin, PosterCreateBaseView):
    """Create communication poster."""

    current_tab = "posters"
    success_url = reverse_lazy("com:poster_list")
    extra_context = {"app": "com"}


class PosterEditView(ComTabsMixin, PosterEditBaseView):
    """Edit communication poster."""

    current_tab = "posters"
    success_url = reverse_lazy("com:poster_list")
    extra_context = {"app": "com"}


class PosterDeleteView(PosterDeleteBaseView):
    """Delete communication poster."""

    success_url = reverse_lazy("com:poster_list")


class PosterModerateListView(PermissionRequiredMixin, ComTabsMixin, ListView):
    """Moderate list communication poster."""

    current_tab = "posters"
    model = Poster
    template_name = "com/poster_moderate.jinja"
    queryset = Poster.objects.filter(is_moderated=False).all()
    permission_required = "com.moderate_poster"
    extra_context = {"app": "com"}


class PosterModerateView(PermissionRequiredMixin, ComTabsMixin, View):
    """Moderate communication poster."""

    current_tab = "posters"
    permission_required = "com.moderate_poster"
    extra_context = {"app": "com"}

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(Poster, pk=kwargs["object_id"])
        obj.is_moderated = True
        obj.moderator = request.user
        obj.save()
        return redirect("com:poster_moderate_list")


class ScreenListView(PermissionRequiredMixin, ComTabsMixin, ListView):
    """List communication screens."""

    current_tab = "screens"
    model = Screen
    template_name = "com/screen_list.jinja"
    permission_required = "com.view_screen"


class ScreenSlideshowView(DetailView):
    """Slideshow of actives posters."""

    pk_url_kwarg = "screen_id"
    model = Screen
    template_name = "com/screen_slideshow.jinja"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "posters": self.object.active_posters()
        }


class ScreenCreateView(PermissionRequiredMixin, ComTabsMixin, CreateView):
    """Create communication screen."""

    current_tab = "screens"
    model = Screen
    fields = ["name"]
    template_name = "core/create.jinja"
    success_url = reverse_lazy("com:screen_list")
    permission_required = "com.add_screen"


class ScreenEditView(PermissionRequiredMixin, ComTabsMixin, UpdateView):
    """Edit communication screen."""

    pk_url_kwarg = "screen_id"
    current_tab = "screens"
    model = Screen
    fields = ["name"]
    template_name = "com/screen_edit.jinja"
    success_url = reverse_lazy("com:screen_list")
    permission_required = "com.change_screen"


class ScreenDeleteView(PermissionRequiredMixin, ComTabsMixin, DeleteView):
    """Delete communication screen."""

    pk_url_kwarg = "screen_id"
    current_tab = "screens"
    model = Screen
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("com:screen_list")
    permission_required = "com.delete_screen"
