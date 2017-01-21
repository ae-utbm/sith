from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django.utils import timezone

from core.models import User, MetaGroup, Group, SithFile

class Forum(models.Model):
    """
    The Forum class, made as a tree to allow nice tidy organization
    """
    name = models.CharField(_('name'), max_length=64)
    description = models.CharField(_('description'), max_length=256, default="")
    is_category = models.BooleanField(_('is a category'), default=False)
    parent = models.ForeignKey('Forum', related_name='children', null=True, blank=True)
    edit_groups = models.ManyToManyField(Group, related_name="editable_forums", blank=True,
            default=[settings.SITH_GROUP_OLD_SUBSCRIBERS_ID])
    view_groups = models.ManyToManyField(Group, related_name="viewable_forums", blank=True,
            default=[settings.SITH_GROUP_PUBLIC_ID])

    def is_owned_by(self, user):
        return user.is_in_group(settings.SITH_GROUP_FORUM_ADMIN_ID)

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list"""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_('You can not make loops in forums'))
            objs.append(cur)
            cur = cur.parent

    def clean(self):
        self.check_loop()

    def __str__(self):
        return "%s" % (self.name)

    def get_absolute_url(self):
        return reverse('forum:view_forum', kwargs={'forum_id': self.id})

    def get_parent_list(self):
        l = []
        p = self.parent
        while p is not None:
            l.append(p)
            p = p.parent
        return l

    def get_topic_number(self):
        number = self.topics.all().count()
        for c in self.children.all():
            number += c.get_topic_number()
        return number

    def get_last_message(self):
        last_msg = None
        for m in ForumMessage.objects.order_by('-id'):
            forum = m.topic.forum
            if self in (forum.get_parent_list() + [forum]):
                return m
                last_msg = m
        try:
            pass
        except: pass
        return last_msg

class ForumTopic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics')
    author = models.ForeignKey(User, related_name='forum_topics')
    title = models.CharField(_("title"), default="", max_length=64)
    description = models.CharField(_('description'), max_length=256, default="")

    class Meta:
        ordering = ['-id'] # TODO: add date message ordering

    def is_owned_by(self, user):
        return self.forum.is_owned_by(user) or user.id == self.author.id

    def can_be_edited_by(self, user):
        return user.can_edit(self.forum)

    def can_be_viewed_by(self, user):
        return user.can_view(self.forum)

    def __str__(self):
        return "%s" % (self.title)

    def get_absolute_url(self):
        return reverse('forum:view_topic', kwargs={'topic_id': self.id})

class ForumMessage(models.Model):
    """
    "A ForumMessage object represents a message in the forum" -- Cpt. Obvious
    """
    topic = models.ForeignKey(ForumTopic, related_name='messages')
    author = models.ForeignKey(User, related_name='forum_messages')
    title = models.CharField(_("title"), default="", max_length=64, blank=True)
    message = models.TextField(_("message"), default="")
    date = models.DateTimeField(_('date'), default=timezone.now)

    class Meta:
        ordering = ['id']

    def is_owned_by(self, user):
        return self.topic.is_owned_by(user) or user.id == self.author.id

    def can_be_edited_by(self, user):
        return user.is_owner(self.topic)

    def can_be_viewed_by(self, user):
        return user.can_view(self.topic)

    def get_absolute_url(self):
        return self.topic.get_absolute_url()

