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
from typing import Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Exists, F, OuterRef, Q
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import Notification, Preferences, User


class Sith(models.Model):
    """A one instance class storing all the modifiable infos."""

    alert_msg = models.TextField(_("alert message"), default="", blank=True)
    info_msg = models.TextField(_("info message"), default="", blank=True)
    weekmail_destinations = models.TextField(_("weekmail destinations"), default="")

    def __str__(self):
        return "⛩ Sith ⛩"

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin


class NewsQuerySet(models.QuerySet):
    def published(self) -> Self:
        return self.filter(is_published=True)

    def waiting_moderation(self) -> Self:
        """Filter all non-finished non-published news"""
        # Because of the way News and NewsDates are created,
        # there may be some cases where this method is called before
        # the NewsDates linked to a Date are actually persisted in db.
        # Thus, it's important to filter by "not past date" rather than by "future date"
        return self.filter(~Q(dates__start_date__lt=timezone.now()), is_published=False)

    def viewable_by(self, user: User) -> Self:
        """Filter news that the given user can view.

        If the user has the `com.view_unmoderated_news` permission,
        all news are viewable.
        Else the viewable news are those that are either moderated
        or authored by the user.
        """
        if user.has_perm("com.view_unmoderated_news"):
            return self
        q_filter = Q(is_published=True)
        if user.is_authenticated:
            q_filter |= Q(author_id=user.id)
        return self.filter(q_filter)


class News(models.Model):
    """News about club events."""

    title = models.CharField(_("title"), max_length=64)
    summary = models.TextField(
        _("summary"),
        help_text=_(
            "A description of the event (what is the activity ? "
            "is there an associated clic ? is there a inscription form ?)"
        ),
    )
    content = models.TextField(
        _("content"),
        blank=True,
        default="",
        help_text=_("A more detailed and exhaustive description of the event."),
    )
    club = models.ForeignKey(
        Club,
        related_name="news",
        verbose_name=_("club"),
        on_delete=models.CASCADE,
        help_text=_("The club which organizes the event."),
    )
    author = models.ForeignKey(
        User,
        related_name="owned_news",
        verbose_name=_("author"),
        on_delete=models.PROTECT,
    )
    is_published = models.BooleanField(_("is published"), default=False)
    moderator = models.ForeignKey(
        User,
        related_name="moderated_news",
        verbose_name=_("moderator"),
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = NewsQuerySet.as_manager()

    class Meta:
        verbose_name = _("news")
        permissions = [
            ("moderate_news", "Can moderate news"),
            ("view_unmoderated_news", "Can view non-moderated news"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.is_published:
            admins_without_notif = User.objects.filter(
                ~Exists(
                    Notification.objects.filter(
                        user=OuterRef("pk"), type="NEWS_MODERATION"
                    )
                ),
                groups__id=settings.SITH_GROUP_COM_ADMIN_ID,
            )
            notif_url = reverse("com:news_admin_list")
            new_notifs = [
                Notification(user=user, url=notif_url, type="NEWS_MODERATION")
                for user in admins_without_notif
            ]
            Notification.objects.bulk_create(new_notifs)
        self.update_moderation_notifs()

    def get_absolute_url(self):
        return reverse("com:news_detail", kwargs={"news_id": self.id})

    def get_full_url(self):
        return f"https://{settings.SITH_URL}{self.get_absolute_url()}"

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin or user == self.author

    def can_be_edited_by(self, user: User):
        return user.is_authenticated and (
            self.author_id == user.id or user.has_perm("com.change_news")
        )

    def can_be_viewed_by(self, user: User):
        return (
            self.is_published
            or user.has_perm("com.view_unmoderated_news")
            or (user.is_authenticated and self.author_id == user.id)
        )

    @staticmethod
    def update_moderation_notifs():
        count = News.objects.waiting_moderation().count()
        notifs_qs = Notification.objects.filter(
            type="NEWS_MODERATION", user__groups__id=settings.SITH_GROUP_COM_ADMIN_ID
        )
        if count:
            notifs_qs.update(viewed=False, param=str(count))
        else:
            notifs_qs.update(viewed=True)


class NewsDateQuerySet(models.QuerySet):
    def viewable_by(self, user: User) -> Self:
        """Filter the event dates that the given user can view.

        - If the can view non moderated news, he can view all news dates
        - else, he can view the dates of news that are either
          authored by him or moderated.
        """
        if user.has_perm("com.view_unmoderated_news"):
            return self
        q_filter = Q(news__is_published=True)
        if user.is_authenticated:
            q_filter |= Q(news__author_id=user.id)
        return self.filter(q_filter)


class NewsDate(models.Model):
    """A date associated with news.

    A [News][com.models.News] can have multiple dates, for example if it is a recurring event.
    """

    news = models.ForeignKey(
        News,
        related_name="dates",
        verbose_name=_("news_date"),
        on_delete=models.CASCADE,
    )
    start_date = models.DateTimeField(_("start_date"))
    end_date = models.DateTimeField(_("end_date"))

    objects = NewsDateQuerySet.as_manager()

    class Meta:
        verbose_name = _("news date")
        verbose_name_plural = _("news dates")
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="news_date_end_date_after_start_date",
            )
        ]

    def __str__(self):
        return f"{self.news.title}: {self.start_date} - {self.end_date}"


class Weekmail(models.Model):
    """The weekmail class.

    :ivar title: Title of the weekmail
    :ivar intro: Introduction of the weekmail
    :ivar joke: Joke of the week
    :ivar protip: Tip of the week
    :ivar conclusion: Conclusion of the weekmail
    :ivar sent: Track if the weekmail has been sent
    """

    title = models.CharField(_("title"), max_length=64, blank=True)
    intro = models.TextField(_("intro"), blank=True)
    joke = models.TextField(_("joke"), blank=True)
    protip = models.TextField(_("protip"), blank=True)
    conclusion = models.TextField(_("conclusion"), blank=True)
    sent = models.BooleanField(_("sent"), default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Weekmail {self.id} (sent: {self.sent}) - {self.title}"

    def send(self):
        """Send the weekmail to all users with the receive weekmail option opt-in.

        Also send the weekmail to the mailing list in settings.SITH_COM_EMAIL.
        """
        dest = [
            i[0]
            for i in Preferences.objects.filter(receive_weekmail=True).values_list(
                "user__email"
            )
        ]
        with transaction.atomic():
            email = EmailMultiAlternatives(
                subject=self.title,
                body=self.render_text(),
                from_email=settings.SITH_COM_EMAIL,
                to=Sith.objects.first().weekmail_destinations.split(" "),
                bcc=dest,
            )
            email.attach_alternative(self.render_html(), "text/html")
            email.send()
            self.sent = True
            self.save()
            Weekmail().save()

    def render_text(self):
        """Renders a pure text version of the mail for readers without HTML support."""
        return render(
            None, "com/weekmail_renderer_text.jinja", context={"weekmail": self}
        ).content.decode("utf-8")

    def render_html(self):
        """Renders an HTML version of the mail with images and fancy CSS."""
        return render(
            None, "com/weekmail_renderer_html.jinja", context={"weekmail": self}
        ).content.decode("utf-8")

    def get_banner(self):
        """Return an absolute link to the banner."""
        return (
            "http://" + settings.SITH_URL + static("com/img/weekmail_bannerV2P22.png")
        )

    def get_footer(self):
        """Return an absolute link to the footer."""
        return "http://" + settings.SITH_URL + static("com/img/weekmail_footerP22.png")

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin


class WeekmailArticle(models.Model):
    weekmail = models.ForeignKey(
        Weekmail,
        related_name="articles",
        verbose_name=_("weekmail"),
        null=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(_("title"), max_length=64)
    content = models.TextField(_("content"))
    author = models.ForeignKey(
        User,
        related_name="owned_weekmail_articles",
        verbose_name=_("author"),
        on_delete=models.CASCADE,
    )
    club = models.ForeignKey(
        Club,
        related_name="weekmail_articles",
        verbose_name=_("club"),
        on_delete=models.CASCADE,
    )
    rank = models.IntegerField(_("rank"), default=-1)

    def __str__(self):
        return "%s - %s (%s)" % (self.title, self.author, self.club)

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin


class Screen(models.Model):
    name = models.CharField(_("name"), max_length=128)

    def __str__(self):
        return self.name

    def active_posters(self):
        now = timezone.now()
        return self.posters.filter(is_moderated=True, date_begin__lte=now).filter(
            Q(date_end__isnull=True) | Q(date_end__gte=now)
        )

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin


class Poster(models.Model):
    name = models.CharField(
        _("name"), blank=False, null=False, max_length=128, default=""
    )
    file = models.ImageField(_("file"), null=False, upload_to="com/posters")
    club = models.ForeignKey(
        Club,
        related_name="posters",
        verbose_name=_("club"),
        null=False,
        on_delete=models.CASCADE,
    )
    screens = models.ManyToManyField(Screen, related_name="posters")
    date_begin = models.DateTimeField(blank=False, null=False, default=timezone.now)
    date_end = models.DateTimeField(blank=True, null=True)
    display_time = models.IntegerField(
        _("display time"), blank=False, null=False, default=15
    )
    is_moderated = models.BooleanField(_("is moderated"), default=False)
    moderator = models.ForeignKey(
        User,
        related_name="moderated_posters",
        verbose_name=_("moderator"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        permissions = [("moderate_poster", "Can moderate poster")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.is_moderated:
            for user in User.objects.filter(
                groups__id__in=[settings.SITH_GROUP_COM_ADMIN_ID]
            ):
                Notification.objects.create(
                    user=user, url=reverse("com:poster_list"), type="POSTER_MODERATION"
                )
        return super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if self.date_end and self.date_begin > self.date_end:
            raise ValidationError(_("Begin date should be before end date"))

    def get_display_name(self):
        return self.club.get_display_name()
