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
from __future__ import annotations

from typing import Self

from django.conf import settings
from django.core import validators
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator, validate_email
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from core.models import Group, MetaGroup, Notification, Page, RealGroup, SithFile, User

# Create your models here.


# This function prevents generating migration upon settings change
def get_default_owner_group():
    return settings.SITH_GROUP_ROOT_ID


class Club(models.Model):
    """The Club class, made as a tree to allow nice tidy organization."""

    id = models.AutoField(primary_key=True, db_index=True)
    name = models.CharField(_("name"), max_length=64)
    parent = models.ForeignKey(
        "Club", related_name="children", null=True, blank=True, on_delete=models.CASCADE
    )
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

    owner_group = models.ForeignKey(
        Group,
        related_name="owned_club",
        default=get_default_owner_group,
        on_delete=models.CASCADE,
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
    page = models.OneToOneField(
        Page, related_name="club", blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["name", "unix_name"]

    def __str__(self):
        return self.name

    @transaction.atomic()
    def save(self, *args, **kwargs):
        old = Club.objects.filter(id=self.id).first()
        creation = old is None
        if not creation and old.unix_name != self.unix_name:
            self._change_unixname(self.unix_name)
        super().save(*args, **kwargs)
        if creation:
            board = MetaGroup(name=self.unix_name + settings.SITH_BOARD_SUFFIX)
            board.save()
            member = MetaGroup(name=self.unix_name + settings.SITH_MEMBER_SUFFIX)
            member.save()
            subscribers = Group.objects.filter(
                name=settings.SITH_MAIN_MEMBERS_GROUP
            ).first()
            self.make_home()
            self.home.edit_groups.set([board])
            self.home.view_groups.set([member, subscribers])
            self.home.save()
        self.make_page()
        cache.set(f"sith_club_{self.unix_name}", self)

    def get_absolute_url(self):
        return reverse("club:club_view", kwargs={"club_id": self.id})

    @cached_property
    def president(self):
        return self.members.filter(
            role=settings.SITH_CLUB_ROLES_ID["President"], end_date=None
        ).first()

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list."""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_("You can not make loops in clubs"))
            objs.append(cur)
            cur = cur.parent

    def clean(self):
        self.check_loop()

    def _change_unixname(self, old_name, new_name):
        c = Club.objects.filter(unix_name=new_name).first()
        if c is None:
            # Update all the groups names
            Group.objects.filter(name=old_name).update(name=new_name)
            Group.objects.filter(name=old_name + settings.SITH_BOARD_SUFFIX).update(
                name=new_name + settings.SITH_BOARD_SUFFIX
            )
            Group.objects.filter(name=old_name + settings.SITH_MEMBER_SUFFIX).update(
                name=new_name + settings.SITH_MEMBER_SUFFIX
            )

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

    def delete(self, *args, **kwargs):
        # Invalidate the cache of this club and of its memberships
        for membership in self.members.ongoing().select_related("user"):
            cache.delete(f"membership_{self.id}_{membership.user.id}")
        cache.delete(f"sith_club_{self.unix_name}")
        super().delete(*args, **kwargs)

    def get_display_name(self):
        return self.name

    def is_owned_by(self, user):
        """Method to see if that object can be super edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_board_member

    def get_full_logo_url(self):
        return "https://%s%s" % (settings.SITH_URL, self.logo.url)

    def can_be_edited_by(self, user):
        """Method to see if that object can be edited by the given user."""
        return self.has_rights_in_club(user)

    def can_be_viewed_by(self, user):
        """Method to see if that object can be seen by the given user."""
        sub = User.objects.filter(pk=user.pk).first()
        if sub is None:
            return False
        return sub.was_subscribed

    def get_membership_for(self, user: User) -> Membership | None:
        """Return the current membership the given user.

        Note:
            The result is cached.
        """
        if user.is_anonymous:
            return None
        membership = cache.get(f"membership_{self.id}_{user.id}")
        if membership == "not_member":
            return None
        if membership is None:
            membership = self.members.filter(user=user, end_date=None).first()
            if membership is None:
                cache.set(f"membership_{self.id}_{user.id}", "not_member")
            else:
                cache.set(f"membership_{self.id}_{user.id}", membership)
        return membership

    def has_rights_in_club(self, user):
        m = self.get_membership_for(user)
        return m is not None and m.role > settings.SITH_MAXIMUM_FREE_ROLE


class MembershipQuerySet(models.QuerySet):
    def ongoing(self) -> Self:
        """Filter all memberships which are not finished yet."""
        return self.filter(Q(end_date=None) | Q(end_date__gt=localdate()))

    def board(self) -> Self:
        """Filter all memberships where the user is/was in the board.

        Be aware that users who were in the board in the past
        are included, even if there are no more members.

        If you want to get the users who are currently in the board,
        mind combining this with the :meth:`ongoing` queryset method
        """
        return self.filter(role__gt=settings.SITH_MAXIMUM_FREE_ROLE)

    def update(self, **kwargs):
        """Refresh the cache for the elements of the queryset.

        Besides that, does the same job as a regular update method.

        Be aware that this adds a db query to retrieve the updated objects
        """
        nb_rows = super().update(**kwargs)
        if nb_rows > 0:
            # if at least a row was affected, refresh the cache
            for membership in self.all():
                if membership.end_date is not None:
                    cache.set(
                        f"membership_{membership.club_id}_{membership.user_id}",
                        "not_member",
                    )
                else:
                    cache.set(
                        f"membership_{membership.club_id}_{membership.user_id}",
                        membership,
                    )

    def delete(self):
        """Work just like the default Django's delete() method,
        but add a cache invalidation for the elements of the queryset
        before the deletion.

        Be aware that this adds a db query to retrieve the deleted element.
        As this first query take place before the deletion operation,
        it will be performed even if the deletion fails.
        """
        ids = list(self.values_list("club_id", "user_id"))
        nb_rows, _ = super().delete()
        if nb_rows > 0:
            for club_id, user_id in ids:
                cache.set(f"membership_{club_id}_{user_id}", "not_member")


class Membership(models.Model):
    """The Membership class makes the connection between User and Clubs.

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
        on_delete=models.CASCADE,
    )
    club = models.ForeignKey(
        Club,
        verbose_name=_("club"),
        related_name="members",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
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

    objects = MembershipQuerySet.as_manager()

    def __str__(self):
        return (
            f"{self.club.name} - {self.user.username} "
            f"- {settings.SITH_CLUB_ROLES[self.role]} "
            f"- {str(_('past member')) if self.end_date is not None else ''}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.end_date is None:
            cache.set(f"membership_{self.club_id}_{self.user_id}", self)
        else:
            cache.set(f"membership_{self.club_id}_{self.user_id}", "not_member")

    def get_absolute_url(self):
        return reverse("club:club_members", kwargs={"club_id": self.club_id})

    def is_owned_by(self, user):
        """Method to see if that object can be super edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_board_member

    def can_be_edited_by(self, user: User) -> bool:
        """Check if that object can be edited by the given user."""
        if user.is_root or user.is_board_member:
            return True
        membership = self.club.get_membership_for(user)
        if membership is not None and membership.role >= self.role:
            return True
        return False

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(f"membership_{self.club_id}_{self.user_id}")


class Mailing(models.Model):
    """A Mailing list for a club.

    Warning:
        Remember that mailing lists should be validated by UTBM.
    """

    club = models.ForeignKey(
        Club,
        verbose_name=_("Club"),
        related_name="mailings",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
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
        User,
        related_name="moderated_mailings",
        verbose_name=_("moderator"),
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return "%s - %s" % (self.club, self.email_full)

    def save(self, *args, **kwargs):
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
                    ).save(*args, **kwargs)
        super().save(*args, **kwargs)

    def clean(self):
        if Mailing.objects.filter(email=self.email).exists():
            raise ValidationError(_("This mailing list already exists."))
        if self.can_moderate(self.moderator):
            self.is_moderated = True
        else:
            self.moderator = None
        super().clean()

    @property
    def email_full(self):
        return self.email + "@" + settings.SITH_MAILING_DOMAIN

    def can_moderate(self, user):
        return user.is_root or user.is_com_admin

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_root or user.is_com_admin

    def can_view(self, user):
        return self.club.has_rights_in_club(user)

    def can_be_edited_by(self, user):
        return self.club.has_rights_in_club(user)

    def delete(self, *args, **kwargs):
        self.subscriptions.all().delete()
        super().delete()

    def fetch_format(self):
        destination = "".join(s.fetch_format() for s in self.subscriptions.all())
        return f"{self.email}: {destination}"


class MailingSubscription(models.Model):
    """Link between user and mailing list."""

    mailing = models.ForeignKey(
        Mailing,
        verbose_name=_("Mailing"),
        related_name="subscriptions",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        related_name="mailing_subscriptions",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(_("Email address"), blank=False, null=False)

    class Meta:
        unique_together = (("user", "email", "mailing"),)

    def __str__(self):
        return "(%s) - %s : %s" % (self.mailing, self.get_username, self.email)

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
        super().clean()

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return (
            self.mailing.club.has_rights_in_club(user)
            or user.is_root
            or self.user.is_com_admin
        )

    def can_be_edited_by(self, user):
        return self.user is not None and user.id == self.user.id

    @cached_property
    def get_email(self):
        if self.user and not self.email:
            return self.user.email
        return self.email

    @cached_property
    def get_username(self):
        if self.user:
            return str(self.user)
        return _("Unregistered user")

    def fetch_format(self):
        return self.get_email + " "
