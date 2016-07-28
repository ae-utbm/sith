from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

from core.models import User
from subscription.models import Subscriber

# Create your models here.

class Launderette(models.Model):
    name = models.CharField(_('name'), max_length=30)
    sellers = models.ManyToManyField(Subscriber, verbose_name=_('sellers'), related_name='launderettes', blank=True)

    class Meta:
        verbose_name = _('Launderette')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['launderette-admin']['name']):
            return True
        return False

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('launderette:launderette_list')

class Machine(models.Model):
    name = models.CharField(_('name'), max_length=30)
    launderette = models.ForeignKey(Launderette, related_name='machines', verbose_name=_('launderette'))
    is_working = models.BooleanField(_('is working'), default=True)

    class Meta:
        verbose_name = _('Machine')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['launderette-admin']['name']):
            return True
        return False

    def __str__(self):
        return "%s - Launderette: %s - Working: %s" % (self.name, self.launderette, self.is_working)

class Token(models.Model):
    name = models.IntegerField(_('name'))
    launderette = models.ForeignKey(Launderette, related_name='tokens', verbose_name=_('launderette'))
    type = models.CharField(_('type'), max_length=10, choices=[('WASHING', _('Washing')), ('DRYING', _('Drying'))])

    class Meta:
        verbose_name = _('Token')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['launderette-admin']['name']):
            return True
        return False

class Slot(models.Model):
    start_date = models.DateTimeField(_('start date'))
    type = models.CharField(_('type'), max_length=10, choices=[('WASHING', _('Washing')), ('DRYING', _('Drying'))])
    machine = models.ForeignKey(Machine, related_name='slots', verbose_name=_('machine'))
    token = models.ForeignKey(Token, related_name='slots', verbose_name=_('token'), blank=True, null=True)
    user = models.ForeignKey(Subscriber, related_name='slots', verbose_name=_('user'))

    class Meta:
        verbose_name = _('Slot')

    def full_clean(self):
        return super(Slot, self).full_clean()

    def __str__(self):
        return str(self.user) + " - " + str(self.start_date)


