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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core import utils
from core.models import Notification, Preferences, RealGroup, User


class Sith(models.Model):
    """A one instance class storing all the modifiable infos"""

    alert_msg = models.TextField(_("alert message"), default="", blank=True)
    info_msg = models.TextField(_("info message"), default="", blank=True)
    weekmail_destinations = models.TextField(_("weekmail destinations"), default="")
    version = utils.get_git_revision_short_hash()

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin

    def __str__(self):
        return "⛩ Sith ⛩"


NEWS_TYPES = [
    ("NOTICE", _("Notice")),
    ("EVENT", _("Event")),
    ("WEEKLY", _("Weekly")),
    ("CALL", _("Call")),
]


class News(models.Model):
    """The news class"""

    title = models.CharField(_("title"), max_length=64)
    summary = models.TextField(_("summary"))
    content = models.TextField(_("content"))
    type = models.CharField(
        _("type"), max_length=16, choices=NEWS_TYPES, default="EVENT"
    )
    club = models.ForeignKey(
        Club, related_name="news", verbose_name=_("club"), on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name="owned_news",
        verbose_name=_("author"),
        on_delete=models.CASCADE,
    )
    is_moderated = models.BooleanField(_("is moderated"), default=False)
    moderator = models.ForeignKey(
        User,
        related_name="moderated_news",
        verbose_name=_("moderator"),
        null=True,
        on_delete=models.CASCADE,
    )

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin or user == self.author

    def can_be_edited_by(self, user):
        return user.is_com_admin

    def can_be_viewed_by(self, user):
        return self.is_moderated or user.is_com_admin

    def get_absolute_url(self):
        return reverse("com:news_detail", kwargs={"news_id": self.id})

    def get_full_url(self):
        return "https://%s%s" % (settings.SITH_URL, self.get_absolute_url())

    def __str__(self):
        return "%s: %s" % (self.type, self.title)

    def save(self, *args, **kwargs):
        super(News, self).save(*args, **kwargs)
        for u in (
            RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID)
            .first()
            .users.all()
        ):
            Notification(
                user=u,
                url=reverse("com:news_admin_list"),
                type="NEWS_MODERATION",
                param="1",
            ).save()


def news_notification_callback(notif):
    count = (
        News.objects.filter(
            Q(dates__start_date__gt=timezone.now(), is_moderated=False)
            | Q(type="NOTICE", is_moderated=False)
        )
        .distinct()
        .count()
    )
    if count:
        notif.viewed = False
        notif.param = "%s" % count
        notif.date = timezone.now()
    else:
        notif.viewed = True


class NewsDate(models.Model):
    """
    A date class, useful for weekly events, or for events that just have no date

    This class allows more flexibilty managing the dates related to a news, particularly when this news is weekly, since
    we don't have to make copies
    """

    news = models.ForeignKey(
        News,
        related_name="dates",
        verbose_name=_("news_date"),
        on_delete=models.CASCADE,
    )
    start_date = models.DateTimeField(_("start_date"), null=True, blank=True)
    end_date = models.DateTimeField(_("end_date"), null=True, blank=True)

    def __str__(self):
        return "%s: %s - %s" % (self.news.title, self.start_date, self.end_date)


class Weekmail(models.Model):
    """
    The weekmail class

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

    def send(self):
        """
        Send the weekmail to all users with the receive weekmail option opt-in.
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
        """
        Renders a pure text version of the mail for readers without HTML support.
        """
        return render(
            None, "com/weekmail_renderer_text.jinja", context={"weekmail": self}
        ).content.decode("utf-8")

    def render_html(self):
        """
        Renders an HTML version of the mail with images and fancy CSS.
        """
        return render(
            None, "com/weekmail_renderer_html.jinja", context={"weekmail": self}
        ).content.decode("utf-8")

    def get_banner(self):
        """
        Return an absolute link to the banner.
        """
        return (
            "http://" + settings.SITH_URL + static("com/img/weekmail_bannerV2P22.png")
        )

    def get_footer(self):
        """
        Return an absolute link to the footer.
        """
        return "http://" + settings.SITH_URL + static("com/img/weekmail_footerP22.png")

    def __str__(self):
        return "Weekmail %s (sent: %s) - %s" % (self.id, self.sent, self.title)

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

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin

    def __str__(self):
        return "%s - %s (%s)" % (self.title, self.author, self.club)


class Screen(models.Model):
    name = models.CharField(_("name"), max_length=128)

    def active_posters(self):
        now = timezone.now()
        return self.posters.filter(is_moderated=True, date_begin__lte=now).filter(
            Q(date_end__isnull=True) | Q(date_end__gte=now)
        )

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin

    def __str__(self):
        return "%s" % (self.name)


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

    def save(self, *args, **kwargs):
        if not self.is_moderated:
            for u in (
                RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID)
                .first()
                .users.all()
            ):
                Notification(
                    user=u,
                    url=reverse("com:poster_moderate_list"),
                    type="POSTER_MODERATION",
                ).save()
        return super(Poster, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if self.date_end and self.date_begin > self.date_end:
            raise ValidationError(_("Begin date should be before end date"))

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_com_admin or len(user.clubs_with_rights) > 0

    def can_be_moderated_by(self, user):
        return user.is_com_admin

    def get_display_name(self):
        return self.club.get_display_name()

    @property
    def page(self):
        return self.club.page

    def __str__(self):
        return self.name
