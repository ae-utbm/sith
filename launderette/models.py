from django.db import models, DataError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

from core.models import User
from counter.models import Counter, Product
from subscription.models import Subscriber
from subscription.views import get_subscriber

# Create your models here.

class Launderette(models.Model):
    name = models.CharField(_('name'), max_length=30)
    counter = models.OneToOneField(Counter, verbose_name=_('counter'), related_name='launderette')

    class Meta:
        verbose_name = _('Launderette')

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['launderette-admin']['name']):
            return True
        return False

    def can_be_edited_by(self, user):
        sub = get_subscriber(user)
        return sub in self.counter.sellers.all()

    def can_be_viewed_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_MEMBERS_GROUP)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('launderette:launderette_list')

class Machine(models.Model):
    name = models.CharField(_('name'), max_length=30)
    launderette = models.ForeignKey(Launderette, related_name='machines', verbose_name=_('launderette'))
    type = models.CharField(_('type'), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES)
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
        return "%s %s" % (self._meta.verbose_name, self.name)

    def get_absolute_url(self):
        return reverse('launderette:launderette_admin', kwargs={"launderette_id": self.launderette.id})

class Token(models.Model):
    name = models.CharField(_('name'), max_length=5)
    launderette = models.ForeignKey(Launderette, related_name='tokens', verbose_name=_('launderette'))
    type = models.CharField(_('type'), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES)
    borrow_date = models.DateTimeField(_('borrow date'), null=True, blank=True)
    user = models.ForeignKey(Subscriber, related_name='tokens', verbose_name=_('user'), null=True, blank=True)

    class Meta:
        verbose_name = _('Token')
        unique_together = ('name', 'launderette', 'type')
        ordering = ['type', 'name']

    def save(self, *args, **kwargs):
        if self.name == "":
            raise DataError(_("Token name can not be blank"))
        else:
            super(Token, self).save(*args, **kwargs)

    def is_owned_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.is_in_group(settings.SITH_GROUPS['launderette-admin']['name']):
            return True
        return False

    def __str__(self):
        return self.__class__._meta.verbose_name + " " + self.get_type_display() + " #" + self.name + " (" + self.launderette.name + ")"

class Slot(models.Model):
    start_date = models.DateTimeField(_('start date'))
    type = models.CharField(_('type'), max_length=10, choices=settings.SITH_LAUNDERETTE_MACHINE_TYPES)
    machine = models.ForeignKey(Machine, related_name='slots', verbose_name=_('machine'))
    token = models.ForeignKey(Token, related_name='slots', verbose_name=_('token'), blank=True, null=True)
    user = models.ForeignKey(Subscriber, related_name='slots', verbose_name=_('user'))

    class Meta:
        verbose_name = _('Slot')
        ordering = ['start_date']

    def __str__(self):
        return "User: %s - Date: %s - Type: %s - Machine: %s - Token: %s" % (self.user, self.start_date, self.get_type_display(),
                self.machine.name, self.token)


