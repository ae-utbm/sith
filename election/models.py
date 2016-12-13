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
    This class allows to create a new election
    """
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)
    start_candidature = models.DateTimeField(_('start candidature'), blank=False)
    end_candidature = models.DateTimeField(_('end candidature'), blank=False)
    start_date = models.DateTimeField(_('start date'), blank=False)
    end_date = models.DateTimeField(_('end date'), blank=False)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return bool(now <= self.end_date and now >= self.start_date)

    @property
    def is_candidature_active(self):
        now = timezone.now()
        return bool(now <= self.end_candidature and now >= self.start_candidature)

    def has_voted(self, user):
        return self.has_voted.filter(id=user.id).exists()

    def get_results(self):
        pass


class Role(models.Model):
    """
    This class allows to create a new role avaliable for a candidature
    """
    election = models.ForeignKey(Election, related_name='role', verbose_name=_("election"))
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)

    def __str__(self):
        return ("%s : %s") % (self.election.title, self.title)


class Candidature(models.Model):
    """
    This class is a component of responsability
    """
    role = models.ForeignKey(Role, related_name='candidature', verbose_name=_("role"))
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='candidate', blank=True)
    program = models.TextField(_('description'), null=True, blank=True)
    has_voted = models.ManyToManyField(User, verbose_name=_('has_voted'), related_name='has_voted')


class List(models.Model):
    """
    To allow per list vote
    """
    title = models.CharField(_('title'))


class Vote(models.Model):
    """
    This class allows to vote for candidates
    """
    role = models.ForeignKey(Role, related_name='vote', verbose_name=_("role"))
    candidature = models.ManyToManyField(Candidature, related_name='vote', verbose_name=_("candidature"))

    def __str__(self):
        return "Vote"