# -*- coding:utf-8 -*
#
# Copyright 2017
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from datetime import timedelta, date

from core.models import User
from club.models import Club

class MatmatManager(models.Manager):
    def get_queryset(self):
        return super(MatmatManager, self).get_queryset()

class AvailableMatmatManager(models.Manager):
    def get_queryset(self):
        return super(AvailableMatmatManager,
                self).get_queryset().filter(subscription_deadline__gte=date.today())

class Matmat(models.Model):
    """
    This is the main class, the Matmat itself.
    It contains the deadlines for the users, and the link to the club that makes
    its Matmatronch.
    """
    subscription_deadline = models.DateField(_('subscription deadline'),
            default=timezone.now, help_text=_("Before this date, users are "
                "allowed to subscribe to this Matmatronch. "
                "After this date, users subscribed will be allowed to comment on each other."))
    comments_deadline = models.DateField(_('comments deadline'),
            default=timezone.now, help_text=_("After this date, users won't be "
                "able to make comments anymore"))
    club = models.OneToOneField(Club, related_name='matmat')

    objects = MatmatManager()
    availables = AvailableMatmatManager()

    def __str__(self):
        return str(self.club.name)

    def clean(self):
        if self.subscription_deadline > self.comments_deadline:
            raise ValidationError(_("Closing the subscriptions after the "
                "comments is definitively not a good idea."))

    def get_absolute_url(self):
        return reverse('matmat:detail', kwargs={'matmat_id': self.id})

    def is_owned_by(self, user):
        return user.is_owner(self.club)

    def can_be_viewed_by(self, user):
        return user.can_edit(self.club)

class MatmatUser(models.Model):
    """
    This class is only here to avoid cross references between the core, club,
    and matmat modules. It binds a User to a Matmat without needing to import
    Matmat into the core.
    """
    user = models.OneToOneField(User, verbose_name=_("matmat user"), related_name='matmat_user')
    matmat = models.ForeignKey(Matmat, verbose_name=_("matmat"), related_name='users', blank=True, null=True, on_delete=models.SET_NULL)

class MatmatComment(models.Model):
    """
    This represent a comment given by someone to someone else in the same Matmat
    instance.
    """
    author = models.ForeignKey(MatmatUser, verbose_name=_("author"), related_name='given_comments')
    target = models.ForeignKey(MatmatUser, verbose_name=_("target"), related_name='received_comments')
    content = models.TextField(_("content"), default="", max_length=400)
    is_moderated = models.BooleanField(_("is moderated"), default=False)

