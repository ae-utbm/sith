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
    start_proposal = models.DateTimeField(_('start proposal'), blank=False)
    end_proposal = models.DateTimeField(_('end proposal'), blank=False)
    start_date = models.DateTimeField(_('start date'), blank=False)
    end_date = models.DateTimeField(_('end date'), blank=False)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return bool(now <= self.end_date and now >= self.start_date)

    @property
    def is_proposal_active(self):
        now = timezone.now()
        return bool(now <= self.end_proposal and now >= self.start_proposal)

    def has_voted(self, user):
        return self.vote.filter(user__id=user.id).exists()

    def get_results(self):
        pass


class Responsability(models.Model):
    """
    This class allows to create a new responsability
    """
    election = models.ForeignKey(Election, related_name='responsability', verbose_name=_("election"))
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)

    def __str__(self):
        return ("%s : %s") % (self.election.title, self.title)


class Candidate(models.Model):
    """
    This class is a component of responsability
    """
    responsability = models.ForeignKey(Responsability, related_name='candidate', verbose_name=_("responsability"))
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='candidate', blank=True)
    program = models.TextField(_('description'), null=True, blank=True)

    def __str__(self):
        return ("%s : %s -> %s") % (self.election.title, self.title, self.user.get_full_name())


class Vote(models.Model):
    """
    This class allows to vote for candidates
    """
    election = models.ForeignKey(Election, related_name='vote', verbose_name=_("election"))
    candidate = models.ManyToManyField(Candidate, related_name='vote', verbose_name=_("candidate"))
    user = models.ForeignKey(User, related_name='vote', verbose_name=_("user"))

    def __str__(self):
        return "Vote"