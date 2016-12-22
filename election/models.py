from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings

from datetime import timedelta
from core.models import User, Group


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

    edit_groups = models.ManyToManyField(Group, related_name="editable_elections", verbose_name=_("edit groups"), blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_elections", verbose_name=_("view groups"), blank=True)
    vote_groups = models.ManyToManyField(Group, related_name="votable_elections", verbose_name=_("vote groups"), blank=True)
    candidature_groups = models.ManyToManyField(Group, related_name="candidate_elections", verbose_name=_("candidature groups"), blank=True)

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
        return hasattr(user, 'has_voted') and user.has_voted.all() == list(self.role.all())

    # Permissions


class Role(models.Model):
    """
    This class allows to create a new role avaliable for a candidature
    """
    election = models.ForeignKey(Election, related_name='role', verbose_name=_("election"))
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), null=True, blank=True)
    has_voted = models.ManyToManyField(User, verbose_name=('has voted'), related_name='has_voted')
    max_choice = models.IntegerField(_('max choice'), default=1)

    def user_has_voted(self, user):
        return self.has_voted.filter(id=user.id).exists()

    def __str__(self):
        return ("%s : %s") % (self.election.title, self.title)


class ElectionList(models.Model):
    """
    To allow per list vote
    """
    title = models.CharField(_('title'), max_length=255)
    election = models.ForeignKey(Election, related_name='election_list', verbose_name=_("election"))

    def __str__(self):
        return self.title


class Candidature(models.Model):
    """
    This class is a component of responsability
    """
    role = models.ForeignKey(Role, related_name='candidature', verbose_name=_("role"))
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='candidate', blank=True)
    program = models.TextField(_('description'), null=True, blank=True)
    election_list = models.ForeignKey(ElectionList, related_name='candidature', verbose_name=_('election_list'))

    def __str__(self):
        return "%s : %s" % (self.role.title, self.user.username)


class Vote(models.Model):
    """
    This class allows to vote for candidates
    """
    role = models.ForeignKey(Role, related_name='vote', verbose_name=_("role"))
    candidature = models.ManyToManyField(Candidature, related_name='vote', verbose_name=_("candidature"))

    def __str__(self):
        return "Vote"