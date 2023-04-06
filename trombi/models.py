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

from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import User
from core.utils import get_semester_code


class TrombiManager(models.Manager):
    def get_queryset(self):
        return super(TrombiManager, self).get_queryset()


class AvailableTrombiManager(models.Manager):
    def get_queryset(self):
        return (
            super(AvailableTrombiManager, self)
            .get_queryset()
            .filter(subscription_deadline__gte=date.today())
        )


class Trombi(models.Model):
    """
    This is the main class, the Trombi itself.
    It contains the deadlines for the users, and the link to the club that makes
    its Trombi.
    """

    subscription_deadline = models.DateField(
        _("subscription deadline"),
        default=date.today,
        help_text=_(
            "Before this date, users are "
            "allowed to subscribe to this Trombi. "
            "After this date, users subscribed will be allowed to comment on each other."
        ),
    )
    comments_deadline = models.DateField(
        _("comments deadline"),
        default=date.today,
        help_text=_(
            "After this date, users won't be " "able to make comments anymore."
        ),
    )
    max_chars = models.IntegerField(
        _("maximum characters"),
        default=400,
        help_text=_("Maximum number of characters allowed in a comment."),
    )
    show_profiles = models.BooleanField(
        _("show users profiles to each other"), default=True
    )
    club = models.OneToOneField(Club, related_name="trombi", on_delete=models.CASCADE)

    objects = TrombiManager()
    availables = AvailableTrombiManager()

    def __str__(self):
        return str(self.club.name)

    def clean(self):
        if self.subscription_deadline > self.comments_deadline:
            raise ValidationError(
                _(
                    "Closing the subscriptions after the "
                    "comments is definitively not a good idea."
                )
            )

    def get_absolute_url(self):
        return reverse("trombi:detail", kwargs={"trombi_id": self.id})

    def is_owned_by(self, user):
        return user.can_edit(self.club)

    def can_be_viewed_by(self, user):
        return user.id in [u.user.id for u in self.users.all()]


class TrombiUser(models.Model):
    """
    This class is only here to avoid cross references between the core, club,
    and trombi modules. It binds a User to a Trombi without needing to import
    Trombi into the core.
    It also adds the pictures to the profile without needing all the security
    like the other SithFiles.
    """

    user = models.OneToOneField(
        User,
        verbose_name=_("trombi user"),
        related_name="trombi_user",
        on_delete=models.CASCADE,
    )
    trombi = models.ForeignKey(
        Trombi,
        verbose_name=_("trombi"),
        related_name="users",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    profile_pict = models.ImageField(
        upload_to="trombi",
        verbose_name=_("profile pict"),
        null=True,
        blank=True,
        help_text=_(
            "The profile picture you want in the trombi (warning: this picture may be published)"
        ),
    )
    scrub_pict = models.ImageField(
        upload_to="trombi",
        verbose_name=_("scrub pict"),
        null=True,
        blank=True,
        help_text=_(
            "The scrub picture you want in the trombi (warning: this picture may be published)"
        ),
    )

    def __str__(self):
        return str(self.user)

    def is_owned_by(self, user):
        return user.is_owner(self.trombi)

    def make_memberships(self):
        self.memberships.all().delete()
        for m in self.user.memberships.filter(
            role__gt=settings.SITH_MAXIMUM_FREE_ROLE
        ).order_by("end_date"):
            role = str(settings.SITH_CLUB_ROLES[m.role])
            if m.description:
                role += " (%s)" % m.description
            if m.end_date:
                end_date = get_semester_code(m.end_date)
            else:
                end_date = ""
            TrombiClubMembership(
                user=self,
                club=str(m.club),
                role=role[:64],
                start=get_semester_code(m.start_date),
                end=end_date,
            ).save()


class TrombiComment(models.Model):
    """
    This represent a comment given by someone to someone else in the same Trombi
    instance.
    """

    author = models.ForeignKey(
        TrombiUser,
        verbose_name=_("author"),
        related_name="given_comments",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        TrombiUser,
        verbose_name=_("target"),
        related_name="received_comments",
        on_delete=models.CASCADE,
    )
    content = models.TextField(_("content"), default="")
    is_moderated = models.BooleanField(_("is the comment moderated"), default=False)

    def can_be_viewed_by(self, user):
        if user.id == self.target.user.id:
            return False
        return user.id == self.author.user.id or user.can_edit(self.author.trombi)


class TrombiClubMembership(models.Model):
    """
    This represent a membership to a club
    """

    user = models.ForeignKey(
        TrombiUser,
        verbose_name=_("user"),
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    club = models.CharField(_("club"), max_length=32, default="")
    role = models.CharField(_("role"), max_length=64, default="")
    start = models.CharField(_("start"), max_length=16, default="")
    end = models.CharField(_("end"), max_length=16, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "%s - %s - %s (%s)" % (self.user, self.club, self.role, self.start)

    def can_be_edited_by(self, user):
        return user.id == self.user.user.id or user.can_edit(self.user.trombi)

    def get_absolute_url(self):
        return reverse("trombi:profile")
