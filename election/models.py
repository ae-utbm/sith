from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings

from datetime import timedelta
from core.models import User
from subscription.models import Subscriber
from subscription.views import get_subscriber


class Election(models.Model):
    """
    This class allow to create a new election
    """
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)
    start_date = models.DateTimeField(_('start date'), blank=False)
    end_date = models.DateTimeField(_('end date'), blank=False)
    electors = models.ManyToManyField(Subscriber, related_name='election', verbose_name=_("electors"), blank=True)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return bool(now <= self.end_date and now >= self.start_date)

    def has_voted(self, user):
        return self.electors.filter(id=user.id).exists()

    def get_results(self):
        pass


class Responsability(models.Model):
    """
    """
    election = models.ForeignKey(Election, related_name='responsability', verbose_name=_("election"))
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)
    blank_votes = models.IntegerField(_('blank votes'), default=0)

    def __str__(self):
        return ("%s : %s") % (self.election.title, self.title)


class Candidate(models.Model):
    """
    """
    responsability = models.ForeignKey(Responsability, related_name='candidate', verbose_name=_("responsability"))
    subscriber = models.ForeignKey(Subscriber, verbose_name=_('user'), related_name='candidate', blank=True)
    program = models.TextField(_('description'), null=True, blank=True)
    votes = models.IntegerField(_('votes'), default=0)

    def __str__(self):
        return ("%s : %s -> %s") % (self.election.title, self.title, self.subscriber.get_full_name())
