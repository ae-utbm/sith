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

from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

from counter.models import Counter
from core.models import User
from club.models import Club

# Create your models here.


class Launderette(models.Model):
    name = models.CharField(_("name"), max_length=30)
    counter = models.OneToOneField(
        Counter, verbose_name=_("counter"), related_name="launderette"
    )

    class Meta:
        verbose_name = _("Launderette")

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
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
        return user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP)

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
        Launderette, related_name="machines", verbose_name=_("launderette")
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
        Launderette, related_name="tokens", verbose_name=_("launderette")
    )
    type = models.CharField(
        _("type"), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES
    )
    borrow_date = models.DateTimeField(_("borrow date"), null=True, blank=True)
    user = models.ForeignKey(
        User, related_name="tokens", verbose_name=_("user"), null=True, blank=True
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
        Machine, related_name="slots", verbose_name=_("machine")
    )
    token = models.ForeignKey(
        Token, related_name="slots", verbose_name=_("token"), blank=True, null=True
    )
    user = models.ForeignKey(User, related_name="slots", verbose_name=_("user"))

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
