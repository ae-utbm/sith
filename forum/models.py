from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from datetime import datetime
import pytz

from core.models import User, MetaGroup, Group, SithFile
from club.models import Club

class Forum(models.Model):
    """
    The Forum class, made as a tree to allow nice tidy organization

    owner_club allows club members to moderate there own topics
    edit_groups allows to put any group as a forum admin
    view_groups allows some groups to view a forum
    """
    name = models.CharField(_('name'), max_length=64)
    description = models.CharField(_('description'), max_length=256, default="")
    is_category = models.BooleanField(_('is a category'), default=False)
    parent = models.ForeignKey('Forum', related_name='children', null=True, blank=True)
    owner_club = models.ForeignKey(Club, related_name="owned_forums", verbose_name=_("owner club"),
            default=settings.SITH_MAIN_CLUB_ID)
    edit_groups = models.ManyToManyField(Group, related_name="editable_forums", blank=True,
            default=[settings.SITH_GROUP_OLD_SUBSCRIBERS_ID])
    view_groups = models.ManyToManyField(Group, related_name="viewable_forums", blank=True,
            default=[settings.SITH_GROUP_PUBLIC_ID])

    def clean(self):
        self.check_loop()

    def save(self, *args, **kwargs):
        copy_rights = False
        if self.id is None:
            copy_rights = True
        super(Forum, self).save(*args, **kwargs)
        if copy_rights:
            self.copy_rights()

    def apply_rights_recursively(self):
        children = self.children.all()
        for c in children:
            c.copy_rights()
            c.apply_rights_recursively()

    def copy_rights(self):
        """Copy, if possible, the rights of the parent folder"""
        if self.parent is not None:
            self.owner_club = self.parent.owner_club
            self.edit_groups = self.parent.edit_groups.all()
            self.view_groups = self.parent.view_groups.all()
            self.save()

    def is_owned_by(self, user):
        if user.is_in_group(settings.SITH_GROUP_FORUM_ADMIN_ID):
            return True
        m = self.owner_club.get_membership_for(user)
        if m:
            return m.role > settings.SITH_MAXIMUM_FREE_ROLE
        return False

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list"""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_('You can not make loops in forums'))
            objs.append(cur)
            cur = cur.parent

    def __str__(self):
        return "%s" % (self.name)

    def get_absolute_url(self):
        return reverse('forum:view_forum', kwargs={'forum_id': self.id})

    @cached_property
    def parent_list(self):
        return self.get_parent_list()

    def get_parent_list(self):
        l = []
        p = self.parent
        while p is not None:
            l.append(p)
            p = p.parent
        return l

    @cached_property
    def topic_number(self):
        return self.get_topic_number()

    def get_topic_number(self):
        number = self.topics.all().count()
        for c in self.children.all():
            number += c.topic_number
        return number

    @cached_property
    def last_message(self):
        return self.get_last_message()

    def get_last_message(self):
        last_msg = None
        for m in ForumMessage.objects.select_related('topic__forum', 'author').order_by('-id'):
            forum = m.topic.forum
            if self in (forum.parent_list + [forum]):
                return m
                last_msg = m
        return last_msg

class ForumTopic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics')
    author = models.ForeignKey(User, related_name='forum_topics')
    description = models.CharField(_('description'), max_length=256, default="")

    class Meta:
        ordering = ['-id'] # TODO: add date message ordering

    def is_owned_by(self, user):
        return self.forum.is_owned_by(user)

    def can_be_edited_by(self, user):
        return user.can_edit(self.forum)

    def can_be_viewed_by(self, user):
        return user.can_view(self.forum)

    def __str__(self):
        return "%s" % (self.title)

    def get_absolute_url(self):
        return reverse('forum:view_topic', kwargs={'topic_id': self.id})

    @property
    def title(self):
        return self.messages.order_by('date').first().title

class ForumMessage(models.Model):
    """
    "A ForumMessage object represents a message in the forum" -- Cpt. Obvious
    """
    topic = models.ForeignKey(ForumTopic, related_name='messages')
    author = models.ForeignKey(User, related_name='forum_messages')
    title = models.CharField(_("title"), default="", max_length=64, blank=True)
    message = models.TextField(_("message"), default="")
    date = models.DateTimeField(_('date'), default=timezone.now)
    readers = models.ManyToManyField(User, related_name="read_messages", verbose_name=_("readers"))

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "%s - %s" % (self.id, self.title)

    def is_owned_by(self, user): # Anyone can create a topic: it's better to
                                 # check the rights at the forum level, since it's more controlled
        return self.topic.forum.is_owned_by(user) or user.id == self.author.id

    def can_be_edited_by(self, user):
        return user.can_edit(self.topic.forum)

    def can_be_viewed_by(self, user):
        return (not self.deleted and user.can_view(self.topic))

    def can_be_moderated_by(self, user):
        return self.topic.forum.is_owned_by(user) or user.id == self.author.id

    def get_absolute_url(self):
        return self.topic.get_absolute_url() + "#msg_" + str(self.id)

    def mark_as_read(self, user):
        try: # Need the try/except because of AnonymousUser
            self.readers.add(user)
        except: pass

    def is_read(self, user):
        return (self.date < user.forum_infos.last_read_date) or (user in self.readers.all())

    @cached_property
    def deleted(self):
        return self.is_deleted()

    def is_deleted(self):
        meta = self.metas.exclude(action="EDIT").order_by('-date').first()
        if meta:
            return meta.action == "DELETE"
        return False

MESSAGE_META_ACTIONS = [
        ('EDIT', _("Message edited by")),
        ('DELETE', _("Message deleted by")),
        ('UNDELETE', _("Message undeleted by")),
        ]

class ForumMessageMeta(models.Model):
    user = models.ForeignKey(User, related_name="forum_message_metas")
    message = models.ForeignKey(ForumMessage, related_name="metas")
    date = models.DateTimeField(_('date'), default=timezone.now)
    action = models.CharField(_("action"), choices=MESSAGE_META_ACTIONS, max_length=16)

class ForumUserInfo(models.Model):
    """
    This currently stores only the last date a user clicked "Mark all as read".
    However, this can be extended with lot of user preferences dedicated to a
    user, such as the favourite topics, the signature, and so on...
    """
    user = models.OneToOneField(User, related_name="_forum_infos") # TODO: see to move that to the User class in order to reduce the number of db queries
    last_read_date = models.DateTimeField(_('last read date'), default=datetime(year=settings.SITH_SCHOOL_START_YEAR,
        month=1, day=1, tzinfo=pytz.UTC))

