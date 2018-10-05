# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.validators import RegexValidator, validate_email
from django.utils.functional import cached_property

from core.models import User, MetaGroup, Group, SithFile, RealGroup, Notification, Page

# Create your models here.


class Club(models.Model):
    """
    The Club class, made as a tree to allow nice tidy organization
    """

    id = models.AutoField(primary_key=True, db_index=True)
    name = models.CharField(_("name"), max_length=64)
    parent = models.ForeignKey("Club", related_name="children", null=True, blank=True)
    unix_name = models.CharField(
        _("unix name"),
        max_length=30,
        unique=True,
        validators=[
            validators.RegexValidator(
                r"^[a-z0-9][a-z0-9._-]*[a-z0-9]$",
                _(
                    "Enter a valid unix name. This value may contain only "
                    "letters, numbers ./-/_ characters."
                ),
            )
        ],
        error_messages={"unique": _("A club with that unix name already exists.")},
    )
    logo = models.ImageField(
        upload_to="club_logos", verbose_name=_("logo"), null=True, blank=True
    )
    is_active = models.BooleanField(_("is active"), default=True)
    short_description = models.CharField(
        _("short description"), max_length=1000, default="", blank=True, null=True
    )
    address = models.CharField(_("address"), max_length=254)
    # This function prevents generating migration upon settings change
    def get_default_owner_group():
        return settings.SITH_GROUP_ROOT_ID

    owner_group = models.ForeignKey(
        Group, related_name="owned_club", default=get_default_owner_group
    )
    edit_groups = models.ManyToManyField(
        Group, related_name="editable_club", blank=True
    )
    view_groups = models.ManyToManyField(
        Group, related_name="viewable_club", blank=True
    )
    home = models.OneToOneField(
        SithFile,
        related_name="home_of_club",
        verbose_name=_("home"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    page = models.OneToOneField(Page, related_name="club", blank=True, null=True)

    class Meta:
        ordering = ["name", "unix_name"]

    @cached_property
    def president(self):
        return self.members.filter(
            role=settings.SITH_CLUB_ROLES_ID["President"], end_date=None
        ).first()

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list"""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_("You can not make loops in clubs"))
            objs.append(cur)
            cur = cur.parent

    def clean(self):
        self.check_loop()

    def _change_unixname(self, new_name):
        c = Club.objects.filter(unix_name=new_name).first()
        if c is None:
            if self.home:
                self.home.name = new_name
                self.home.save()
        else:
            raise ValidationError(_("A club with that unix_name already exists"))

    def make_home(self):
        if not self.home:
            home_root = SithFile.objects.filter(parent=None, name="clubs").first()
            root = User.objects.filter(username="root").first()
            if home_root and root:
                home = SithFile(parent=home_root, name=self.unix_name, owner=root)
                home.save()
                self.home = home
                self.save()

    def make_page(self):
        root = User.objects.filter(username="root").first()
        if not self.page:
            club_root = Page.objects.filter(name=settings.SITH_CLUB_ROOT_PAGE).first()
            if root and club_root:
                public = Group.objects.filter(id=settings.SITH_GROUP_PUBLIC_ID).first()
                p = Page(name=self.unix_name)
                p.parent = club_root
                p.save(force_lock=True)
                if public:
                    p.view_groups.add(public)
                p.save(force_lock=True)
                if self.parent and self.parent.page:
                    p.parent = self.parent.page
                self.page = p
                self.save()
        elif self.page and self.page.name != self.unix_name:
            self.page.unset_lock()
            self.page.name = self.unix_name
            self.page.save(force_lock=True)
        elif (
            self.page
            and self.parent
            and self.parent.page
            and self.page.parent != self.parent.page
        ):
            self.page.unset_lock()
            self.page.parent = self.parent.page
            self.page.save(force_lock=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            creation = False
            old = Club.objects.filter(id=self.id).first()
            if not old:
                creation = True
            else:
                if old.unix_name != self.unix_name:
                    self._change_unixname(self.unix_name)
            super(Club, self).save(*args, **kwargs)
            if creation:
                board = MetaGroup(name=self.unix_name + settings.SITH_BOARD_SUFFIX)
                board.save()
                member = MetaGroup(name=self.unix_name + settings.SITH_MEMBER_SUFFIX)
                member.save()
                subscribers = Group.objects.filter(
                    name=settings.SITH_MAIN_MEMBERS_GROUP
                ).first()
                self.make_home()
                self.home.edit_groups = [board]
                self.home.view_groups = [member, subscribers]
                self.home.save()
            self.make_page()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("club:club_view", kwargs={"club_id": self.id})

    def get_display_name(self):
        return self.name

    def is_owned_by(self, user):
        """
        Method to see if that object can be super edited by the given user
        """
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP)

    def get_full_logo_url(self):
        return "https://%s%s" % (settings.SITH_URL, self.logo.url)

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        return self.has_rights_in_club(user)

    def can_be_viewed_by(self, user):
        """
        Method to see if that object can be seen by the given user
        """
        sub = User.objects.filter(pk=user.pk).first()
        if sub is None:
            return False
        return sub.was_subscribed

    _memberships = {}

    def get_membership_for(self, user):
        """
        Returns the current membership the given user
        """
        try:
            return Club._memberships[self.id][user.id]
        except:
            m = self.members.filter(user=user.id).filter(end_date=None).first()
            try:
                Club._memberships[self.id][user.id] = m
            except:
                Club._memberships[self.id] = {}
                Club._memberships[self.id][user.id] = m
            return m

    def has_rights_in_club(self, user):
        m = self.get_membership_for(user)
        return m is not None and m.role > settings.SITH_MAXIMUM_FREE_ROLE


class Membership(models.Model):
    """
    The Membership class makes the connection between User and Clubs

    Both Users and Clubs can have many Membership objects:
       - a user can be a member of many clubs at a time
       - a club can have many members at a time too

    A User is currently member of all the Clubs where its Membership has an end_date set to null/None.
    Otherwise, it's a past membership kept because it can be very useful to see who was in which Club in the past.
    """

    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        related_name="memberships",
        null=False,
        blank=False,
    )
    club = models.ForeignKey(
        Club, verbose_name=_("club"), related_name="members", null=False, blank=False
    )
    start_date = models.DateField(_("start date"), default=timezone.now)
    end_date = models.DateField(_("end date"), null=True, blank=True)
    role = models.IntegerField(
        _("role"),
        choices=sorted(settings.SITH_CLUB_ROLES.items()),
        default=sorted(settings.SITH_CLUB_ROLES.items())[0][0],
    )
    description = models.CharField(
        _("description"), max_length=128, null=False, blank=True
    )

    def clean(self):
        sub = User.objects.filter(pk=self.user.pk).first()
        if sub is None or not sub.is_subscribed:
            raise ValidationError(_("User must be subscriber to take part to a club"))
        if (
            Membership.objects.filter(user=self.user)
            .filter(club=self.club)
            .filter(end_date=None)
            .exists()
        ):
            raise ValidationError(_("User is already member of that club"))

    def __str__(self):
        return (
            self.club.name
            + " - "
            + self.user.username
            + " - "
            + str(settings.SITH_CLUB_ROLES[self.role])
            + str(" - " + str(_("past member")) if self.end_date is not None else "")
        )

    def is_owned_by(self, user):
        """
        Method to see if that object can be super edited by the given user
        """
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP)

    def can_be_edited_by(self, user):
        """
        Method to see if that object can be edited by the given user
        """
        if user.memberships:
            ms = user.memberships.filter(club=self.club, end_date=None).first()
            return (ms and ms.role >= self.role) or user.is_in_group(
                settings.SITH_MAIN_BOARD_GROUP
            )
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP)

    def get_absolute_url(self):
        return reverse("club:club_members", kwargs={"club_id": self.club.id})


class Mailing(models.Model):
    """
    This class correspond to a mailing list
    Remember that mailing lists should be validated by UTBM
    """

    club = models.ForeignKey(
        Club, verbose_name=_("Club"), related_name="mailings", null=False, blank=False
    )
    email = models.CharField(
        _("Email address"),
        unique=True,
        null=False,
        blank=False,
        max_length=256,
        validators=[
            RegexValidator(
                validate_email.user_regex,
                _("Enter a valid address. Only the root of the address is needed."),
            )
        ],
    )
    is_moderated = models.BooleanField(_("is moderated"), default=False)
    moderator = models.ForeignKey(
        User, related_name="moderated_mailings", verbose_name=_("moderator"), null=True
    )

    def clean(self):
        if self.can_moderate(self.moderator):
            self.is_moderated = True
        else:
            self.moderator = None
        super(Mailing, self).clean()

    @property
    def email_full(self):
        return self.email + "@" + settings.SITH_MAILING_DOMAIN

    def can_moderate(self, user):
        return user.is_root or user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)

    def is_owned_by(self, user):
        return (
            user.is_in_group(self)
            or user.is_root
            or user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)
        )

    def can_view(self, user):
        return self.club.has_rights_in_club(user)

    def can_be_edited_by(self, user):
        return self.club.has_rights_in_club(user)

    def delete(self):
        for sub in self.subscriptions.all():
            sub.delete()
        super(Mailing, self).delete()

    def fetch_format(self):
        resp = self.email + ": "
        for sub in self.subscriptions.all():
            resp += sub.fetch_format()
        return resp

    def save(self):
        if not self.is_moderated:
            for user in (
                RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID)
                .first()
                .users.all()
            ):
                if not user.notifications.filter(
                    type="MAILING_MODERATION", viewed=False
                ).exists():
                    Notification(
                        user=user,
                        url=reverse("com:mailing_admin"),
                        type="MAILING_MODERATION",
                    ).save()
        super(Mailing, self).save()

    def __str__(self):
        return "%s - %s" % (self.club, self.email_full)


class MailingSubscription(models.Model):
    """
    This class makes the link between user and mailing list
    """

    mailing = models.ForeignKey(
        Mailing,
        verbose_name=_("Mailing"),
        related_name="subscriptions",
        null=False,
        blank=False,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        related_name="mailing_subscriptions",
        null=True,
        blank=True,
    )
    email = models.EmailField(_("Email address"), blank=False, null=False)

    class Meta:
        unique_together = (("user", "email", "mailing"),)

    def clean(self):
        if not self.user and not self.email:
            raise ValidationError(_("At least user or email is required"))
        try:
            if self.user and not self.email:
                self.email = self.user.email
                if MailingSubscription.objects.filter(
                    mailing=self.mailing, email=self.email
                ).exists():
                    raise ValidationError(
                        _("This email is already suscribed in this mailing")
                    )
        except ObjectDoesNotExist:
            pass
        super(MailingSubscription, self).clean()

    def is_owned_by(self, user):
        return (
            self.mailing.club.has_rights_in_club(user)
            or user.is_root
            or self.user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)
        )

    def can_be_edited_by(self, user):
        return self.user is not None and user.id == self.user.id

    @property
    def get_email(self):
        if self.user and not self.email:
            return self.user.email
        return self.email

    def fetch_format(self):
        return self.get_email + " "

    def __str__(self):
        if self.user:
            user = str(self.user)
        else:
            user = _("Unregistered user")
        return "(%s) - %s : %s" % (self.mailing, user, self.email)
