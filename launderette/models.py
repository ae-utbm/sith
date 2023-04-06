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
from django.db import DataError, models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import User
from counter.models import Counter

# Create your models here.


class Launderette(models.Model):
    name = models.CharField(_("name"), max_length=30)
    counter = models.OneToOneField(
        Counter,
        verbose_name=_("counter"),
        related_name="launderette",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Launderette")

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        launderette_club = Club.objects.filter(
            unix_name=settings.SITH_LAUNDERETTE_MANAGER["unix_name"]
        ).first()
        m = launderette_club.get_membership_for(user)
        if m and m.role >= 9:
            return True
        return False

    def can_be_edited_by(self, user):
        launderette_club = Club.objects.filter(
            unix_name=settings.SITH_LAUNDERETTE_MANAGER["unix_name"]
        ).first()
        m = launderette_club.get_membership_for(user)
        if m and m.role >= 2:
            return True
        return False

    def can_be_viewed_by(self, user):
        return user.is_subscribed

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("launderette:launderette_list")

    def get_machine_list(self):
        return Machine.objects.filter(launderette_id=self.id)

    def machine_list(self):
        return [m.id for m in self.get_machine_list()]

    def get_token_list(self):
        return Token.objects.filter(launderette_id=self.id)

    def token_list(self):
        return [t.id for t in self.get_token_list()]


class Machine(models.Model):
    name = models.CharField(_("name"), max_length=30)
    launderette = models.ForeignKey(
        Launderette,
        related_name="machines",
        verbose_name=_("launderette"),
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        _("type"), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES
    )
    is_working = models.BooleanField(_("is working"), default=True)

    class Meta:
        verbose_name = _("Machine")

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        launderette_club = Club.objects.filter(
            unix_name=settings.SITH_LAUNDERETTE_MANAGER["unix_name"]
        ).first()
        m = launderette_club.get_membership_for(user)
        if m and m.role >= 9:
            return True
        return False

    def __str__(self):
        return "%s %s" % (self._meta.verbose_name, self.name)

    def get_absolute_url(self):
        return reverse(
            "launderette:launderette_admin",
            kwargs={"launderette_id": self.launderette.id},
        )


class Token(models.Model):
    name = models.CharField(_("name"), max_length=5)
    launderette = models.ForeignKey(
        Launderette,
        related_name="tokens",
        verbose_name=_("launderette"),
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        _("type"), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES
    )
    borrow_date = models.DateTimeField(_("borrow date"), null=True, blank=True)
    user = models.ForeignKey(
        User,
        related_name="tokens",
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Token")
        unique_together = ("name", "launderette", "type")
        ordering = ["type", "name"]

    def save(self, *args, **kwargs):
        if self.name == "":
            raise DataError(_("Token name can not be blank"))
        else:
            super(Token, self).save(*args, **kwargs)

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_anonymous:
            return False
        launderette_club = Club.objects.filter(
            unix_name=settings.SITH_LAUNDERETTE_MANAGER["unix_name"]
        ).first()
        m = launderette_club.get_membership_for(user)
        if m and m.role >= 9:
            return True
        return False

    def __str__(self):
        return (
            self.__class__._meta.verbose_name
            + " "
            + self.get_type_display()
            + " #"
            + self.name
            + " ("
            + self.launderette.name
            + ")"
        )

    def is_avaliable(self):
        if not self.borrow_date and not self.user:
            return True
        else:
            return False


class Slot(models.Model):
    start_date = models.DateTimeField(_("start date"))
    type = models.CharField(
        _("type"), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES
    )
    machine = models.ForeignKey(
        Machine,
        related_name="slots",
        verbose_name=_("machine"),
        on_delete=models.CASCADE,
    )
    token = models.ForeignKey(
        Token,
        related_name="slots",
        verbose_name=_("token"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User, related_name="slots", verbose_name=_("user"), on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Slot")
        ordering = ["start_date"]

    def is_owned_by(self, user):
        return user == self.user

    def __str__(self):
        return "User: %s - Date: %s - Type: %s - Machine: %s - Token: %s" % (
            self.user,
            self.start_date,
            self.get_type_display(),
            self.machine.name,
            self.token,
        )
