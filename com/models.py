from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy, reverse
from django.conf import settings

from core.models import User
from club.models import Club

class Sith(models.Model):
    """A one instance class storing all the modifiable infos"""
    alert_msg = models.TextField(_("alert message"), default="", blank=True)
    info_msg = models.TextField(_("info message"), default="", blank=True)
    index_page = models.TextField(_("index page"), default="", blank=True)

    def is_owned_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)

    def __str__(self):
        return "⛩ Sith ⛩"

NEWS_TYPES = [
        ('NOTICE', _('Notice')),
        ('EVENT', _('Event')),
        ('WEEKLY', _('Weekly')),
        ('CALL', _('Call')),
        ]

class News(models.Model):
    """The news class"""
    title = models.CharField(_("title"), max_length=64)
    summary = models.TextField(_("summary"))
    content = models.TextField(_("content"))
    type = models.CharField(_("type"), max_length=16, choices=NEWS_TYPES, default="EVENT")
    club = models.ForeignKey(Club, related_name="news", verbose_name=_("club"))
    owner = models.ForeignKey(User, related_name="owned_news", verbose_name=_("owner"))
    is_moderated = models.BooleanField(_("is moderated"), default=False)
    moderator = models.ForeignKey(User, related_name="moderated_news", verbose_name=_("owner"), null=True)

    def get_absolute_url(self):
        return reverse('com:news_detail', kwargs={'news_id': self.id})

    def __str__(self):
        return "%s: %s" % (self.type, self.title)

class NewsDate(models.Model):
    """
    A date class, useful for weekly events, or for events that just have no date

    This class allows more flexibilty managing the dates related to a news, particularly when this news is weekly, since
    we don't have to make copies
    """
    news = models.ForeignKey(News, related_name="dates", verbose_name=_("news_date"))
    start_date = models.DateTimeField(_('start_date'), null=True, blank=True)
    end_date = models.DateTimeField(_('end_date'), null=True, blank=True)

    def __str__(self):
        return "%s: %s - %s" % (self.news.title, self.start_date, self.end_date)
