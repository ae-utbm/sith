# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from datetime import datetime
from itertools import chain

import pytz
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.models import Group, User


class Forum(models.Model):
    """
    The Forum class, made as a tree to allow nice tidy organization

    owner_club allows club members to moderate there own topics
    edit_groups allows to put any group as a forum admin
    view_groups allows some groups to view a forum
    """

    # Those functions prevent generating migration upon settings changes
    def get_default_edit_group():
        return [settings.SITH_GROUP_OLD_SUBSCRIBERS_ID]

    def get_default_view_group():
        return [settings.SITH_GROUP_PUBLIC_ID]

    id = models.AutoField(primary_key=True, db_index=True)
    name = models.CharField(_("name"), max_length=64)
    description = models.CharField(_("description"), max_length=512, default="")
    is_category = models.BooleanField(_("is a category"), default=False)
    parent = models.ForeignKey(
        "Forum",
        related_name="children",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    owner_club = models.ForeignKey(
        Club,
        related_name="owned_forums",
        verbose_name=_("owner club"),
        default=settings.SITH_MAIN_CLUB_ID,
        on_delete=models.CASCADE,
    )
    edit_groups = models.ManyToManyField(
        Group,
        related_name="editable_forums",
        blank=True,
        default=get_default_edit_group,
    )
    view_groups = models.ManyToManyField(
        Group,
        related_name="viewable_forums",
        blank=True,
        default=get_default_view_group,
    )
    number = models.IntegerField(
        _("number to choose a specific forum ordering"), default=1
    )
    _last_message = models.ForeignKey(
        "ForumMessage",
        related_name="forums_where_its_last",
        verbose_name=_("the last message"),
        null=True,
        on_delete=models.SET_NULL,
    )
    _topic_number = models.IntegerField(_("number of topics"), default=0)

    class Meta:
        ordering = ["number"]

    def clean(self):
        self.check_loop()

    def save(self, *args, **kwargs):
        copy_rights = False
        if self.id is None:
            copy_rights = True
        super(Forum, self).save(*args, **kwargs)
        if copy_rights:
            self.copy_rights()

    def set_topic_number(self):
        self._topic_number = self.get_topic_number()
        self.save()
        if self.parent:
            self.parent.set_topic_number()

    def set_last_message(self):
        topic = (
            ForumTopic.objects.filter(forum__id=self.id)
            .exclude(_last_message=None)
            .order_by("-_last_message__id")
            .first()
        )
        forum = (
            Forum.objects.filter(parent__id=self.id)
            .exclude(_last_message=None)
            .order_by("-_last_message__id")
            .first()
        )
        if topic and forum:
            if topic._last_message_id < forum._last_message_id:
                self._last_message_id = forum._last_message_id
            else:
                self._last_message_id = topic._last_message_id
        elif topic:
            self._last_message_id = topic._last_message_id
        elif forum:
            self._last_message_id = forum._last_message_id
        self.save()
        if self.parent:
            self.parent.set_last_message()

    def apply_rights_recursively(self):
        children = self.children.all()
        for c in children:
            c.copy_rights()
            c.apply_rights_recursively()

    def copy_rights(self):
        """Copy, if possible, the rights of the parent folder"""
        if self.parent is not None:
            self.owner_club = self.parent.owner_club
            self.edit_groups.set(self.parent.edit_groups.all())
            self.view_groups.set(self.parent.view_groups.all())
            self.save()

    _club_memberships = {}  # This cache is particularly efficient:

    # divided by 3 the number of requests on the main forum page
    # after the first load
    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        if user.is_in_group(pk=settings.SITH_GROUP_FORUM_ADMIN_ID):
            return True
        try:
            m = Forum._club_memberships[self.id][user.id]
        except:
            m = self.owner_club.get_membership_for(user)
            try:
                Forum._club_memberships[self.id][user.id] = m
            except:
                Forum._club_memberships[self.id] = {}
                Forum._club_memberships[self.id][user.id] = m
        if m:
            return m.role > settings.SITH_MAXIMUM_FREE_ROLE
        return False

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list"""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_("You can not make loops in forums"))
            objs.append(cur)
            cur = cur.parent

    def __str__(self):
        return "%s" % (self.name)

    def get_full_name(self):
        return "/".join(
            chain.from_iterable(
                [[parent.name for parent in self.get_parent_list()], [self.name]]
            )
        )

    def get_absolute_url(self):
        return reverse("forum:view_forum", kwargs={"forum_id": self.id})

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

    @property
    def topic_number(self):
        return self._topic_number

    def get_topic_number(self):
        number = self.topics.all().count()
        for c in self.children.all():
            number += c.topic_number
        return number

    @cached_property
    def last_message(self):
        return self._last_message

    def get_children_list(self):
        l = [self.id]
        for c in self.children.all():
            l.append(c.id)
            l += c.get_children_list()
        return l


class ForumTopic(models.Model):
    forum = models.ForeignKey(Forum, related_name="topics", on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, related_name="forum_topics", on_delete=models.CASCADE
    )
    description = models.CharField(_("description"), max_length=256, default="")
    subscribed_users = models.ManyToManyField(
        User, related_name="favorite_topics", verbose_name=_("subscribed users")
    )
    _last_message = models.ForeignKey(
        "ForumMessage",
        related_name="+",
        verbose_name=_("the last message"),
        null=True,
        on_delete=models.SET_NULL,
    )
    _title = models.CharField(_("title"), max_length=64, blank=True)
    _message_number = models.IntegerField(_("number of messages"), default=0)

    class Meta:
        ordering = ["-_last_message__date"]

    def save(self, *args, **kwargs):
        super(ForumTopic, self).save(*args, **kwargs)
        self.forum.set_topic_number()  # Recompute the cached value
        self.forum.set_last_message()

    def is_owned_by(self, user):
        return self.forum.is_owned_by(user)

    def can_be_edited_by(self, user):
        return user.can_edit(self.forum)

    def can_be_viewed_by(self, user):
        return user.can_view(self.forum)

    def __str__(self):
        return "%s" % (self.title)

    def get_absolute_url(self):
        return reverse("forum:view_topic", kwargs={"topic_id": self.id})

    def get_first_unread_message(self, user):
        try:
            msg = (
                self.messages.exclude(readers=user)
                .filter(date__gte=user.forum_infos.last_read_date)
                .order_by("id")
                .first()
            )
            return msg
        except:
            return None

    @cached_property
    def last_message(self):
        return self._last_message

    @cached_property
    def title(self):
        return self._title


class ForumMessage(models.Model):
    """
    "A ForumMessage object represents a message in the forum" -- Cpt. Obvious
    """

    topic = models.ForeignKey(
        ForumTopic, related_name="messages", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="forum_messages", on_delete=models.CASCADE
    )
    title = models.CharField(_("title"), default="", max_length=64, blank=True)
    message = models.TextField(_("message"), default="")
    date = models.DateTimeField(_("date"), default=timezone.now)
    readers = models.ManyToManyField(
        User, related_name="read_messages", verbose_name=_("readers")
    )
    _deleted = models.BooleanField(_("is deleted"), default=False)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return "%s (%s) - %s" % (self.id, self.author, self.title)

    def save(self, *args, **kwargs):
        self._deleted = self.is_deleted()  # Recompute the cached value
        super(ForumMessage, self).save(*args, **kwargs)
        if self.is_last_in_topic():
            self.topic._last_message_id = self.id
        if self.is_first_in_topic() and self.title:
            self.topic._title = self.title
        self.topic._message_number = self.topic.messages.count()
        self.topic.save()

    def is_first_in_topic(self):
        return bool(self.id == self.topic.messages.order_by("date").first().id)

    def is_last_in_topic(self):
        return bool(self.id == self.topic.messages.order_by("date").last().id)

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        # Anyone can create a topic: it's better to
        # check the rights at the forum level, since it's more controlled
        return self.topic.forum.is_owned_by(user) or user.id == self.author.id

    def can_be_edited_by(self, user):
        return user.can_edit(self.topic.forum)

    def can_be_viewed_by(self, user):
        # No need to check the real rights since it's already done by the Topic view
        # and it impacts performances too much
        return not self._deleted

    def can_be_moderated_by(self, user):
        return self.topic.forum.is_owned_by(user) or user.id == self.author.id

    def get_absolute_url(self):
        return reverse("forum:view_message", kwargs={"message_id": self.id})

    def get_url(self):
        return (
            self.topic.get_absolute_url()
            + "?page="
            + str(self.get_page())
            + "#msg_"
            + str(self.id)
        )

    def get_page(self):
        return (
            int(
                self.topic.messages.filter(id__lt=self.id).count()
                / settings.SITH_FORUM_PAGE_LENGTH
            )
            + 1
        )

    def mark_as_read(self, user):
        try:  # Need the try/except because of AnonymousUser
            if not self.is_read(user):
                self.readers.add(user)
        except:
            pass

    def is_read(self, user):
        return (self.date < user.forum_infos.last_read_date) or (
            user in self.readers.all()
        )

    def is_deleted(self):
        meta = self.metas.exclude(action="EDIT").order_by("-date").first()
        if meta:
            return meta.action == "DELETE"
        return False


MESSAGE_META_ACTIONS = [
    ("EDIT", _("Message edited by")),
    ("DELETE", _("Message deleted by")),
    ("UNDELETE", _("Message undeleted by")),
]


class ForumMessageMeta(models.Model):
    user = models.ForeignKey(
        User, related_name="forum_message_metas", on_delete=models.CASCADE
    )
    message = models.ForeignKey(
        ForumMessage, related_name="metas", on_delete=models.CASCADE
    )
    date = models.DateTimeField(_("date"), default=timezone.now)
    action = models.CharField(_("action"), choices=MESSAGE_META_ACTIONS, max_length=16)

    def save(self, *args, **kwargs):
        super(ForumMessageMeta, self).save(*args, **kwargs)
        self.message._deleted = self.message.is_deleted()
        self.message.save()


class ForumUserInfo(models.Model):
    """
    This currently stores only the last date a user clicked "Mark all as read".
    However, this can be extended with lot of user preferences dedicated to a
    user, such as the favourite topics, the signature, and so on...
    """

    user = models.OneToOneField(
        User, related_name="_forum_infos", on_delete=models.CASCADE
    )
    last_read_date = models.DateTimeField(
        _("last read date"),
        default=datetime(
            year=settings.SITH_SCHOOL_START_YEAR, month=1, day=1, tzinfo=pytz.UTC
        ),
    )

    def __str__(self):
        return str(self.user)
