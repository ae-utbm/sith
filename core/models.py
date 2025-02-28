#
# Copyright 2016,2017,2018
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
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
from __future__ import annotations

import importlib
import logging
import os
import string
import unicodedata
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Self
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.models import AnonymousUser as AuthAnonymousUser
from django.contrib.auth.models import Group as AuthGroup
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import validators
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Exists, F, OuterRef, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.timezone import localdate, now
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile
    from pydantic import NonNegativeInt

    from club.models import Club


class Group(AuthGroup):
    """Wrapper around django.auth.Group"""

    is_manually_manageable = models.BooleanField(
        _("Is manually manageable"),
        default=False,
        help_text=_("If False, this shouldn't be shown on group management pages"),
    )
    description = models.TextField(_("description"))

    def get_absolute_url(self) -> str:
        return reverse("core:group_list")

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.set(f"sith_group_{self.id}", self)
        cache.set(f"sith_group_{self.name.replace(' ', '_')}", self)

    def delete(self, *args, **kwargs) -> None:
        super().delete(*args, **kwargs)
        cache.delete(f"sith_group_{self.id}")
        cache.delete(f"sith_group_{self.name.replace(' ', '_')}")


def validate_promo(value: int) -> None:
    start_year = settings.SITH_SCHOOL_START_YEAR
    delta = (localdate() + timedelta(days=180)).year - start_year
    if value < 0 or delta < value:
        raise ValidationError(
            _("%(value)s is not a valid promo (between 0 and %(end)s)"),
            params={"value": value, "end": delta},
        )


def get_group(*, pk: int | None = None, name: str | None = None) -> Group | None:
    """Search for a group by its primary key or its name.
    Either one of the two must be set.

    The result is cached for the default duration (should be 5 minutes).

    Args:
        pk: The primary key of the group
        name: The name of the group

    Returns:
        The group if it exists, else None

    Raises:
        ValueError: If no group matches the criteria
    """
    if pk is None and name is None:
        raise ValueError("Either pk or name must be set")

    # replace space characters to hide warnings with memcached backend
    pk_or_name: str | int = pk if pk is not None else name.replace(" ", "_")
    group = cache.get(f"sith_group_{pk_or_name}")

    if group == "not_found":
        # Using None as a cache value is a little bit tricky,
        # so we use a special string to represent None
        return None
    elif group is not None:
        return group
    # if this point is reached, the group is not in cache
    if pk is not None:
        group = Group.objects.filter(pk=pk).first()
    else:
        group = Group.objects.filter(name=name).first()
    if group is not None:
        name = group.name.replace(" ", "_")
        cache.set_many({f"sith_group_{group.id}": group, f"sith_group_{name}": group})
    else:
        cache.set(f"sith_group_{pk_or_name}", "not_found")
    return group


class BanGroup(AuthGroup):
    """An anti-group, that removes permissions instead of giving them.

    Users are linked to BanGroups through UserBan objects.

    Example:
        ```python
        user = User.objects.get(username="...")
        ban_group = BanGroup.objects.first()
        UserBan.objects.create(user=user, ban_group=ban_group, reason="...")

        assert user.ban_groups.contains(ban_group)
        ```
    """

    description = models.TextField(_("description"))

    class Meta:
        verbose_name = _("ban group")
        verbose_name_plural = _("ban groups")


class UserQuerySet(models.QuerySet):
    def filter_inactive(self) -> Self:
        from counter.models import Refilling, Selling
        from subscription.models import Subscription

        threshold = now() - settings.SITH_ACCOUNT_INACTIVITY_DELTA
        subscriptions = Subscription.objects.filter(
            member_id=OuterRef("pk"), subscription_end__gt=localdate(threshold)
        )
        refills = Refilling.objects.filter(
            customer__user_id=OuterRef("pk"), date__gt=threshold
        )
        purchases = Selling.objects.filter(
            customer__user_id=OuterRef("pk"), date__gt=threshold
        )
        return self.exclude(
            Q(Exists(subscriptions)) | Q(Exists(refills)) | Q(Exists(purchases))
        )


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    # see https://docs.djangoproject.com/fr/stable/topics/migrations/#model-managers
    pass


class User(AbstractUser):
    """Defines the base user class, useable in every app.

    This is almost the same as the auth module AbstractUser since it inherits from it,
    but some fields are required, and the username is generated automatically with the
    name of the user (see generate_username()).

    Added field: nick_name, date_of_birth
    Required fields: email, first_name, last_name, date_of_birth
    """

    first_name = models.CharField(_("first name"), max_length=64)
    last_name = models.CharField(_("last name"), max_length=64)
    email = models.EmailField(_("email address"), unique=True)
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)
    nick_name = models.CharField(_("nick name"), max_length=64, null=True, blank=True)
    last_update = models.DateTimeField(_("last update"), auto_now=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="users",
    )
    ban_groups = models.ManyToManyField(
        BanGroup,
        verbose_name=_("ban groups"),
        through="UserBan",
        help_text=_("The bans this user has received."),
        related_name="users",
    )
    home = models.OneToOneField(
        "SithFile",
        related_name="home_of",
        verbose_name=_("home"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    profile_pict = models.OneToOneField(
        "SithFile",
        related_name="profile_of",
        verbose_name=_("profile"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    avatar_pict = models.OneToOneField(
        "SithFile",
        related_name="avatar_of",
        verbose_name=_("avatar"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    scrub_pict = models.OneToOneField(
        "SithFile",
        related_name="scrub_of",
        verbose_name=_("scrub"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    sex = models.CharField(
        _("sex"),
        max_length=10,
        null=True,
        blank=True,
        choices=[("MAN", _("Man")), ("WOMAN", _("Woman")), ("OTHER", _("Other"))],
    )
    pronouns = models.CharField(_("pronouns"), max_length=64, blank=True, default="")
    tshirt_size = models.CharField(
        _("tshirt size"),
        max_length=5,
        choices=[
            ("-", _("-")),
            ("XS", _("XS")),
            ("S", _("S")),
            ("M", _("M")),
            ("L", _("L")),
            ("XL", _("XL")),
            ("XXL", _("XXL")),
            ("XXXL", _("XXXL")),
        ],
        default="-",
    )
    role = models.CharField(
        _("role"),
        max_length=15,
        choices=[
            ("STUDENT", _("Student")),
            ("ADMINISTRATIVE", _("Administrative agent")),
            ("TEACHER", _("Teacher")),
            ("AGENT", _("Agent")),
            ("DOCTOR", _("Doctor")),
            ("FORMER STUDENT", _("Former student")),
            ("SERVICE", _("Service")),
        ],
        blank=True,
        default="",
    )
    department = models.CharField(
        _("department"),
        max_length=15,
        choices=settings.SITH_PROFILE_DEPARTMENTS,
        default="NA",
        blank=True,
    )
    dpt_option = models.CharField(
        _("dpt option"), max_length=32, blank=True, default=""
    )
    semester = models.CharField(_("semester"), max_length=5, blank=True, default="")
    quote = models.CharField(_("quote"), max_length=256, blank=True, default="")
    school = models.CharField(_("school"), max_length=80, blank=True, default="")
    promo = models.IntegerField(
        _("promo"), validators=[validate_promo], null=True, blank=True
    )
    forum_signature = models.TextField(
        _("forum signature"), max_length=256, blank=True, default=""
    )
    second_email = models.EmailField(_("second email address"), null=True, blank=True)
    phone = PhoneNumberField(_("phone"), null=True, blank=True)
    parent_phone = PhoneNumberField(_("parent phone"), null=True, blank=True)
    address = models.CharField(_("address"), max_length=128, blank=True, default="")
    parent_address = models.CharField(
        _("parent address"), max_length=128, blank=True, default=""
    )
    is_subscriber_viewable = models.BooleanField(
        _("is subscriber viewable"), default=True
    )
    godfathers = models.ManyToManyField("User", related_name="godchildren", blank=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.get_display_name()

    def save(self, *args, **kwargs):
        adding = self._state.adding
        with transaction.atomic():
            if not adding:
                old = User.objects.filter(id=self.id).first()
                if old and old.username != self.username:
                    self._change_username(self.username)
            super().save(*args, **kwargs)
            if adding:
                # All users are in the public group.
                self.groups.add(settings.SITH_GROUP_PUBLIC_ID)

    def get_absolute_url(self) -> str:
        return reverse("core:user_profile", kwargs={"user_id": self.pk})

    def promo_has_logo(self) -> bool:
        return Path(
            settings.BASE_DIR / f"core/static/core/img/promo_{self.promo}.png"
        ).exists()

    @cached_property
    def was_subscribed(self) -> bool:
        if "is_subscribed" in self.__dict__ and self.is_subscribed:
            # if the user is currently subscribed, he is an old subscriber too
            # if the property has already been cached, avoid another request
            return True
        return self.subscriptions.exists()

    @cached_property
    def is_subscribed(self) -> bool:
        if "was_subscribed" in self.__dict__ and not self.was_subscribed:
            # if the user never subscribed, he cannot be a subscriber now.
            # if the property has already been cached, avoid another request
            return False
        return self.subscriptions.filter(
            subscription_start__lte=timezone.now(), subscription_end__gte=timezone.now()
        ).exists()

    @cached_property
    def account_balance(self):
        if hasattr(self, "customer"):
            return self.customer.amount
        else:
            return 0

    def is_in_group(self, *, pk: int | None = None, name: str | None = None) -> bool:
        """Check if this user is in the given group.
        Either a group id or a group name must be provided.
        If both are passed, only the id will be considered.

        The group will be fetched using the given parameter.
        If no group is found, return False.
        If a group is found, check if this user is in the latter.

        Returns:
             True if the user is the group, else False
        """
        if pk is not None:
            group: Optional[Group] = get_group(pk=pk)
        elif name is not None:
            group: Optional[Group] = get_group(name=name)
        else:
            raise ValueError("You must either provide the id or the name of the group")
        if group is None:
            return False
        if group.id == settings.SITH_GROUP_SUBSCRIBERS_ID:
            return self.is_subscribed
        if group.id == settings.SITH_GROUP_ROOT_ID:
            return self.is_root
        return group in self.cached_groups

    @property
    def cached_groups(self) -> list[Group]:
        """Get the list of groups this user is in.

        The result is cached for the default duration (should be 5 minutes)

        Returns: A list of all the groups this user is in.
        """
        groups = cache.get(f"user_{self.id}_groups")
        if groups is None:
            groups = list(self.groups.all())
            cache.set(f"user_{self.id}_groups", groups)
        return groups

    @cached_property
    def is_root(self) -> bool:
        if self.is_superuser:
            return True
        root_id = settings.SITH_GROUP_ROOT_ID
        return any(g.id == root_id for g in self.cached_groups)

    @cached_property
    def is_board_member(self) -> bool:
        return self.groups.filter(club_board=settings.SITH_MAIN_CLUB_ID).exists()

    @cached_property
    def is_launderette_manager(self):
        from club.models import Club

        return Club.objects.get(
            id=settings.SITH_LAUNDERETTE_CLUB_ID
        ).get_membership_for(self)

    @cached_property
    def is_banned_alcohol(self) -> bool:
        return self.ban_groups.filter(id=settings.SITH_GROUP_BANNED_ALCOHOL_ID).exists()

    @cached_property
    def is_banned_counter(self) -> bool:
        return self.ban_groups.filter(id=settings.SITH_GROUP_BANNED_COUNTER_ID).exists()

    @cached_property
    def age(self) -> int:
        """Return the age this user has the day the method is called.
        If the user has not filled his age, return 0.
        """
        if self.date_of_birth is None:
            return 0
        today = timezone.now()
        age = today.year - self.date_of_birth.year
        # remove a year if this year's birthday is yet to come
        age -= (today.month, today.day) < (
            self.date_of_birth.month,
            self.date_of_birth.day,
        )
        return age

    def make_home(self):
        if self.home is None:
            home_root = SithFile.objects.filter(parent=None, name="users").first()
            if home_root is not None:
                home = SithFile(parent=home_root, name=self.username, owner=self)
                home.save()
                self.home = home
                self.save()

    def _change_username(self, new_name):
        u = User.objects.filter(username=new_name).first()
        if u is None:
            if self.home:
                self.home.name = new_name
                self.home.save()
        else:
            raise ValidationError(_("A user with that username already exists"))

    def get_profile(self):
        return {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "nick_name": self.nick_name,
            "date_of_birth": self.date_of_birth,
        }

    def get_short_name(self):
        """Returns the short name for the user."""
        if self.nick_name:
            return self.nick_name
        return self.first_name + " " + self.last_name

    def get_display_name(self) -> str:
        """Returns the display name of the user.

        A nickname if possible, otherwise, the full name.
        """
        if self.nick_name:
            return "%s (%s)" % (self.get_full_name(), self.nick_name)
        return self.get_full_name()

    def get_family(
        self,
        godfathers_depth: NonNegativeInt = 4,
        godchildren_depth: NonNegativeInt = 4,
    ) -> set[User.godfathers.through]:
        """Get the family of the user, with the given depth.

        Args:
            godfathers_depth: The number of generations of godfathers to fetch
            godchildren_depth: The number of generations of godchildren to fetch

        Returns:
            A list of family relationships in this user's family
        """
        res = []
        for depth, key, reverse_key in [
            (godfathers_depth, "from_user_id", "to_user_id"),
            (godchildren_depth, "to_user_id", "from_user_id"),
        ]:
            if depth == 0:
                continue
            links = list(User.godfathers.through.objects.filter(**{key: self.id}))
            res.extend(links)
            for _ in range(1, depth):  # noqa: F402 we don't care about gettext here
                ids = [getattr(c, reverse_key) for c in links]
                links = list(
                    User.godfathers.through.objects.filter(
                        **{f"{key}__in": ids}
                    ).exclude(id__in=[r.id for r in res])
                )
                if not links:
                    break
                res.extend(links)
        return set(res)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def generate_username(self) -> str:
        """Generates a unique username based on the first and last names.

        For example: Guy Carlier gives gcarlier, and gcarlier1 if the first one exists.

        Returns:
            The generated username.
        """

        def remove_accents(data):
            return "".join(
                x
                for x in unicodedata.normalize("NFKD", data)
                if unicodedata.category(x)[0] == "L"
            ).lower()

        user_name = (
            remove_accents(self.first_name[0] + self.last_name)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        # load all usernames which could conflict with the new one.
        # we need to actually load them, instead of performing a count,
        # because we cannot be sure that two usernames refer to the
        # actual same word (eg. tmore and tmoreau)
        possible_conflicts: list[str] = list(
            User.objects.filter(username__startswith=user_name).values_list(
                "username", flat=True
            )
        )
        nb_conflicts = sum(
            1 for name in possible_conflicts if name.rstrip(string.digits) == user_name
        )
        if nb_conflicts > 0:
            user_name += str(nb_conflicts)  # exemple => exemple1
        self.username = user_name
        return user_name

    def is_owner(self, obj):
        """Determine if the object is owned by the user."""
        if hasattr(obj, "is_owned_by") and obj.is_owned_by(self):
            return True
        if hasattr(obj, "owner_group") and self.is_in_group(pk=obj.owner_group.id):
            return True
        return self.is_root

    def can_edit(self, obj):
        """Determine if the object can be edited by the user."""
        if hasattr(obj, "can_be_edited_by") and obj.can_be_edited_by(self):
            return True
        if hasattr(obj, "edit_groups"):
            for pk in obj.edit_groups.values_list("pk", flat=True):
                if self.is_in_group(pk=pk):
                    return True
        if isinstance(obj, User) and obj == self:
            return True
        return self.is_owner(obj)

    def can_view(self, obj):
        """Determine if the object can be viewed by the user."""
        if hasattr(obj, "can_be_viewed_by") and obj.can_be_viewed_by(self):
            return True
        if hasattr(obj, "view_groups"):
            for pk in obj.view_groups.values_list("pk", flat=True):
                if self.is_in_group(pk=pk):
                    return True
        return self.can_edit(obj)

    def can_be_edited_by(self, user):
        return user.is_root or user.is_board_member

    def can_be_viewed_by(self, user):
        return (user.was_subscribed and self.is_subscriber_viewable) or user.is_root

    def get_mini_item(self):
        return """
    <div class="mini_profile_link" >
    <span>
    <img src="%s" alt="%s" />
    </span>
    <em>%s</em>
    </a>
    """ % (
            (
                self.profile_pict.get_download_url()
                if self.profile_pict
                else staticfiles_storage.url("core/img/unknown.jpg")
            ),
            _("Profile"),
            escape(self.get_display_name()),
        )

    @cached_property
    def preferences(self):
        if hasattr(self, "_preferences"):
            return self._preferences
        return Preferences.objects.create(user=self)

    @cached_property
    def forum_infos(self):
        if hasattr(self, "_forum_infos"):
            return self._forum_infos
        from forum.models import ForumUserInfo

        return ForumUserInfo.objects.create(user=self)

    @cached_property
    def clubs_with_rights(self) -> list[Club]:
        """The list of clubs where the user has rights"""
        memberships = self.memberships.ongoing().board().select_related("club")
        return [m.club for m in memberships]

    @cached_property
    def is_com_admin(self):
        return self.is_in_group(pk=settings.SITH_GROUP_COM_ADMIN_ID)


class AnonymousUser(AuthAnonymousUser):
    def __init__(self):
        super().__init__()

    @property
    def was_subscribed(self):
        return False

    @property
    def is_subscribed(self):
        return False

    @property
    def subscribed(self):
        return False

    @property
    def is_root(self):
        return False

    @property
    def is_board_member(self):
        return False

    @property
    def is_launderette_manager(self):
        return False

    @property
    def is_banned_alcohol(self):
        return False

    @property
    def is_banned_counter(self):
        return False

    @property
    def forum_infos(self):
        raise PermissionDenied

    @property
    def favorite_topics(self):
        raise PermissionDenied

    def is_in_group(self, *, pk: int | None = None, name: str | None = None) -> bool:
        """The anonymous user is only in the public group."""
        allowed_id = settings.SITH_GROUP_PUBLIC_ID
        if pk is not None:
            return pk == allowed_id
        elif name is not None:
            group = get_group(name=name)
            return group is not None and group.id == allowed_id
        else:
            raise ValueError("You must either provide the id or the name of the group")

    def is_owner(self, obj):
        return False

    def can_edit(self, obj):
        return False

    @property
    def is_com_admin(self):
        return False

    def can_view(self, obj):
        if (
            hasattr(obj, "view_groups")
            and obj.view_groups.filter(id=settings.SITH_GROUP_PUBLIC_ID).exists()
        ):
            return True
        return hasattr(obj, "can_be_viewed_by") and obj.can_be_viewed_by(self)

    def get_display_name(self):
        return _("Visitor")


class UserBan(models.Model):
    """A ban of a user.

    A user can be banned for a specific reason, for a specific duration.
    The expiration date is indicative, and the ban should be removed manually.
    """

    ban_group = models.ForeignKey(
        BanGroup,
        verbose_name=_("ban type"),
        related_name="user_bans",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User, verbose_name=_("user"), related_name="bans", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(
        _("expires at"),
        null=True,
        blank=True,
        help_text=_(
            "When the ban should be removed. "
            "Currently, there is no automatic removal, so this is purely indicative. "
            "Automatic ban removal may be implemented later on."
        ),
    )
    reason = models.TextField(_("reason"))

    class Meta:
        verbose_name = _("user ban")
        verbose_name_plural = _("user bans")
        constraints = [
            models.UniqueConstraint(
                fields=["ban_group", "user"], name="unique_ban_type_per_user"
            ),
            models.CheckConstraint(
                check=Q(expires_at__gte=F("created_at")),
                name="user_ban_end_after_start",
            ),
        ]

    def __str__(self):
        return f"Ban of user {self.user.id}"


class Preferences(models.Model):
    user = models.OneToOneField(
        User, related_name="_preferences", on_delete=models.CASCADE
    )
    receive_weekmail = models.BooleanField(_("receive the Weekmail"), default=False)
    show_my_stats = models.BooleanField(_("show your stats to others"), default=False)
    notify_on_click = models.BooleanField(
        _("get a notification for every click"), default=False
    )
    notify_on_refill = models.BooleanField(
        _("get a notification for every refilling"), default=False
    )

    def __str__(self):
        return f"Preferences of {self.user}"

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def get_display_name(self):
        return self.user.get_display_name()


def get_directory(instance, filename):
    return ".{0}/{1}".format(instance.get_parent_path(), filename)


def get_compressed_directory(instance, filename):
    return "./.compressed/{0}/{1}".format(instance.get_parent_path(), filename)


def get_thumbnail_directory(instance, filename):
    return "./.thumbnails/{0}/{1}".format(instance.get_parent_path(), filename)


class SithFile(models.Model):
    name = models.CharField(_("file name"), max_length=256, blank=False)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        verbose_name=_("parent"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to=get_directory,
        verbose_name=_("file"),
        max_length=256,
        null=True,
        blank=True,
    )
    compressed = models.FileField(
        upload_to=get_compressed_directory,
        verbose_name=_("compressed file"),
        max_length=256,
        null=True,
        blank=True,
    )
    thumbnail = models.FileField(
        upload_to=get_thumbnail_directory,
        verbose_name=_("thumbnail"),
        max_length=256,
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        User,
        related_name="owned_files",
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
    )
    edit_groups = models.ManyToManyField(
        Group, related_name="editable_files", verbose_name=_("edit group"), blank=True
    )
    view_groups = models.ManyToManyField(
        Group, related_name="viewable_files", verbose_name=_("view group"), blank=True
    )
    is_folder = models.BooleanField(_("is folder"), default=True, db_index=True)
    mime_type = models.CharField(_("mime type"), max_length=30)
    size = models.IntegerField(_("size"), default=0)
    date = models.DateTimeField(_("date"), default=timezone.now)
    is_moderated = models.BooleanField(_("is moderated"), default=False)
    moderator = models.ForeignKey(
        User,
        related_name="moderated_files",
        verbose_name=_("owner"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    asked_for_removal = models.BooleanField(_("asked for removal"), default=False)
    is_in_sas = models.BooleanField(
        _("is in the SAS"), default=False, db_index=True
    )  # Allows to query this flag, updated at each call to save()

    class Meta:
        verbose_name = _("file")

    def __str__(self):
        return self.get_parent_path() + "/" + self.name

    def save(self, *args, **kwargs):
        sas = SithFile.objects.filter(id=settings.SITH_SAS_ROOT_DIR_ID).first()
        self.is_in_sas = sas in self.get_parent_list() or self == sas
        adding = self._state.adding
        super().save(*args, **kwargs)
        if adding:
            self.copy_rights()
        if self.is_in_sas:
            for user in User.objects.filter(
                groups__id__in=[settings.SITH_GROUP_SAS_ADMIN_ID]
            ):
                Notification(
                    user=user,
                    url=reverse("sas:moderation"),
                    type="SAS_MODERATION",
                    param="1",
                ).save()

    def is_owned_by(self, user: User) -> bool:
        if user.is_anonymous:
            return False
        if user.is_root:
            return True
        if hasattr(self, "profile_of"):
            # if the `profile_of` attribute is set, this file is a profile picture
            # and profile pictures may only be edited by board members
            return user.is_board_member
        if user.is_com_admin:
            return True
        if self.is_in_sas and user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID):
            return True
        return user.id == self.owner_id

    def can_be_viewed_by(self, user: User) -> bool:
        if hasattr(self, "profile_of"):
            return user.can_view(self.profile_of)
        if hasattr(self, "avatar_of"):
            return user.can_view(self.avatar_of)
        if hasattr(self, "scrub_of"):
            return user.can_view(self.scrub_of)
        return False

    def delete(self, *args, **kwargs):
        for c in self.children.all():
            c.delete()
        self.file.delete()
        if self.compressed:
            self.compressed.delete()
        if self.thumbnail:
            self.thumbnail.delete()
        return super().delete()

    def clean(self):
        """Cleans up the file."""
        super().clean()
        if "/" in self.name:
            raise ValidationError(_("Character '/' not authorized in name"))
        if self == self.parent:
            raise ValidationError(_("Loop in folder tree"), code="loop")
        if self == self.parent or (
            self.parent is not None and self in self.get_parent_list()
        ):
            raise ValidationError(_("Loop in folder tree"), code="loop")
        if self.parent and self.parent.is_file:
            raise ValidationError(
                _("You can not make a file be a children of a non folder file")
            )
        if (
            self.parent is None
            and SithFile.objects.exclude(id=self.id)
            .filter(parent=None, name=self.name)
            .exists()
        ) or (
            self.parent
            and self.parent.children.exclude(id=self.id).filter(name=self.name).exists()
        ):
            raise ValidationError(_("Duplicate file"), code="duplicate")
        if self.is_folder:
            if self.file:
                try:
                    Image.open(BytesIO(self.file.read()))
                except Image.UnidentifiedImageError as e:
                    raise ValidationError(
                        _("This is not a valid folder thumbnail")
                    ) from e
            self.mime_type = "inode/directory"
        if self.is_file and (self.file is None or self.file == ""):
            raise ValidationError(_("You must provide a file"))

    def apply_rights_recursively(self, *, only_folders: bool = False) -> None:
        """Apply the rights of this file to all children recursively.

        Args:
            only_folders: If True, only apply the rights to SithFiles that are folders.
        """
        file_ids = []
        explored_ids = [self.id]
        while len(explored_ids) > 0:  # find all children recursively
            file_ids.extend(explored_ids)
            next_level = SithFile.objects.filter(parent_id__in=explored_ids)
            if only_folders:
                next_level = next_level.filter(is_folder=True)
            explored_ids = list(next_level.values_list("id", flat=True))
        for through in (SithFile.view_groups.through, SithFile.edit_groups.through):
            # force evaluation. Without this, the iterator yields nothing
            groups = list(
                through.objects.filter(sithfile_id=self.id).values_list(
                    "group_id", flat=True
                )
            )
            # delete previous rights
            through.objects.filter(sithfile_id__in=file_ids).delete()
            through.objects.bulk_create(  # create new rights
                [through(sithfile_id=f, group_id=g) for f in file_ids for g in groups]
            )

    def copy_rights(self):
        """Copy, if possible, the rights of the parent folder."""
        if self.parent is not None:
            self.edit_groups.set(self.parent.edit_groups.all())
            self.view_groups.set(self.parent.view_groups.all())

    def move_to(self, parent):
        """Move a file to a new parent.
        `parent` must be a SithFile with the `is_folder=True` property. Otherwise, this function doesn't change
        anything.
        This is done only at the DB level, so that it's very fast for the user. Indeed, this function doesn't modify
        SithFiles recursively, so it stays efficient even with top-level folders.
        """
        if not parent.is_folder:
            return
        self.parent = parent
        self.clean()
        self.save()

    def _repair_fs(self):
        """Rebuilds recursively the filesystem as it should be regarding the DB tree."""
        if self.is_folder:
            for c in self.children.all():
                c._repair_fs()
            return
        elif not self._check_path_consistence():
            # First get future parent path and the old file name
            # Prepend "." so that we match all relative handling of Django's
            # file storage
            parent_path = "." + self.parent.get_full_path()
            parent_full_path = settings.MEDIA_ROOT + parent_path
            os.makedirs(parent_full_path, exist_ok=True)
            old_path = self.file.name  # Should be relative: "./users/skia/bleh.jpg"
            new_path = "." + self.get_full_path()
            try:
                # Make this atomic, so that a FS problem rolls back the DB change
                with transaction.atomic():
                    # Set the new filesystem path
                    self.file.name = new_path
                    self.save()
                    # Really move at the FS level
                    if os.path.exists(parent_full_path):
                        os.rename(
                            settings.MEDIA_ROOT + old_path,
                            settings.MEDIA_ROOT + new_path,
                        )
                        # Empty directories may remain, but that's not really a
                        # problem, and that can be solved with a simple shell
                        # command: `find . -type d -empty -delete`
            except Exception as e:
                logging.error(e)

    def _check_path_consistence(self):
        file_path = str(self.file)
        file_full_path = settings.MEDIA_ROOT + file_path
        db_path = ".%s" % self.get_full_path()
        if not os.path.exists(file_full_path):
            print("%s: WARNING: real file does not exists!" % self.id)  # noqa T201
            print("file path: %s" % file_path, end="")  # noqa T201
            print("  db path: %s" % db_path)  # noqa T201
            return False
        if file_path != db_path:
            print("%s: " % self.id, end="")  # noqa T201
            print("file path: %s" % file_path, end="")  # noqa T201
            print("  db path: %s" % db_path)  # noqa T201
            return False
        return True

    def _check_fs(self):
        if self.is_folder:
            for c in self.children.all():
                c._check_fs()
            return
        else:
            self._check_path_consistence()

    @property
    def is_file(self):
        return not self.is_folder

    @cached_property
    def as_picture(self):
        from sas.models import Picture

        return Picture.objects.filter(id=self.id).first()

    @cached_property
    def as_album(self):
        from sas.models import Album

        return Album.objects.filter(id=self.id).first()

    def get_parent_list(self):
        parents = []
        current = self.parent
        while current is not None:
            parents.append(current)
            current = current.parent
        return parents

    def get_parent_path(self):
        return "/" + "/".join([p.name for p in self.get_parent_list()[::-1]])

    def get_full_path(self):
        return self.get_parent_path() + "/" + self.name

    def get_display_name(self):
        return self.name

    def get_download_url(self):
        return reverse("core:download", kwargs={"file_id": self.id})


class QuickUploadImage(models.Model):
    """Images uploaded by user outside of the SithFile mechanism"""

    IMAGE_NAME_SIZE = 100
    UUID_4_SIZE = 36

    uuid = models.CharField(max_length=UUID_4_SIZE, blank=False, primary_key=True)
    name = models.CharField(max_length=IMAGE_NAME_SIZE, blank=False)
    image = models.ImageField(upload_to="upload")
    content_type = models.CharField(max_length=50, blank=False)
    uploader = models.ForeignKey(
        "User",
        related_name="quick_uploads",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    date = models.DateTimeField(_("date"), auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}{Path(self.image.path).suffix}"

    def get_absolute_url(self):
        return reverse("core:uploaded_image", kwargs={"image_uuid": self.uuid})

    @classmethod
    def create_from_uploaded(
        cls, image: UploadedFile, uploader: User | None = None
    ) -> Self:
        def convert_image(file: UploadedFile) -> ContentFile:
            content = BytesIO()
            Image.open(BytesIO(file.read())).save(
                fp=content, format="webp", optimize=True
            )
            return ContentFile(content.getvalue())

        identifier = str(uuid4())
        name = Path(image.name).stem[: cls.IMAGE_NAME_SIZE - 1]
        file = File(convert_image(image), name=f"{identifier}.webp")

        return cls.objects.create(
            uuid=identifier,
            name=name,
            image=file,
            content_type="image/webp",
            uploader=uploader,
        )


class LockError(Exception):
    """There was a lock error on the object."""

    pass


class AlreadyLocked(LockError):
    """The object is already locked."""

    pass


class NotLocked(LockError):
    """The object is not locked."""

    pass


# This function prevents generating migration upon settings change
def get_default_owner_group():
    return settings.SITH_GROUP_ROOT_ID


class Page(models.Model):
    """The page class to build a Wiki
    Each page may have a parent and it's URL is of the form my.site/page/<grd_pa>/<parent>/<mypage>
    It has an ID field, but don't use it, since it's only there for DB part, and because compound primary key is
    awkward!
    Prefere querying pages with Page.get_page_by_full_name().

    Be careful with the _full_name attribute: this field may not be valid until you call save(). It's made for fast
    query, but don't rely on it when playing with a Page object, use get_full_name() instead!
    """

    name = models.CharField(
        _("page unix name"),
        max_length=30,
        validators=[
            validators.RegexValidator(
                r"^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$",
                _(
                    "Enter a valid page name. This value may contain only "
                    "unaccented letters, numbers "
                    "and ./+/-/_ characters."
                ),
            )
        ],
        blank=False,
    )
    parent = models.ForeignKey(
        "self",
        related_name="children",
        verbose_name=_("parent"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # Attention: this field may not be valid until you call save(). It's made for fast query, but don't rely on it when
    # playing with a Page object, use get_full_name() instead!
    _full_name = models.CharField(_("page name"), max_length=255, blank=True)

    owner_group = models.ForeignKey(
        Group,
        related_name="owned_page",
        verbose_name=_("owner group"),
        default=get_default_owner_group,
        on_delete=models.CASCADE,
    )
    edit_groups = models.ManyToManyField(
        Group, related_name="editable_page", verbose_name=_("edit group"), blank=True
    )
    view_groups = models.ManyToManyField(
        Group, related_name="viewable_page", verbose_name=_("view group"), blank=True
    )
    lock_user = models.ForeignKey(
        User,
        related_name="locked_pages",
        verbose_name=_("lock user"),
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )
    lock_timeout = models.DateTimeField(
        _("lock_timeout"), null=True, blank=True, default=None
    )

    class Meta:
        unique_together = ("name", "parent")
        permissions = (
            ("change_prop_page", "Can change the page's properties (groups, ...)"),
        )

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        """Performs some needed actions before and after saving a page in database."""
        locked = kwargs.pop("force_lock", False)
        if not locked:
            locked = self.is_locked()
        if not locked:
            raise NotLocked("The page is not locked and thus can not be saved")
        self.full_clean()
        if not self.id:
            super().save(
                *args, **kwargs
            )  # Save a first time to correctly set _full_name
        # This reset the _full_name just before saving to maintain a coherent field quicker for queries than the
        # recursive method
        # It also update all the children to maintain correct names
        self._full_name = self.get_full_name()
        for c in self.children.all():
            c.save()
        super().save(*args, **kwargs)
        self.unset_lock()

    def get_absolute_url(self):
        return reverse("core:page", kwargs={"page_name": self._full_name})

    @staticmethod
    def get_page_by_full_name(name):
        """Quicker to get a page with that method rather than building the request every time."""
        return Page.objects.filter(_full_name=name).first()

    def clean(self):
        """Cleans up only the name for the moment, but this can be used to make any treatment before saving the object."""
        if "/" in self.name:
            self.name = self.name.split("/")[-1]
        if (
            Page.objects.exclude(pk=self.pk)
            .filter(_full_name=self.get_full_name())
            .exists()
        ):
            raise ValidationError(_("Duplicate page"), code="duplicate")
        super().clean()
        if self.parent is not None and self in self.get_parent_list():
            raise ValidationError(_("Loop in page tree"), code="loop")

    def can_be_edited_by(self, user):
        if hasattr(self, "club") and self.club.can_be_edited_by(user):
            # Override normal behavior for clubs
            return True
        return self.name == settings.SITH_CLUB_ROOT_PAGE and user.is_board_member

    def can_be_viewed_by(self, user):
        return self.is_club_page

    def get_parent_list(self):
        parents = []
        current = self.parent
        while current is not None:
            parents.append(current)
            current = current.parent
        return parents

    def is_locked(self):
        """Is True if the page is locked, False otherwise.

        This is where the timeout is handled,
        so a locked page for which the timeout is reach will be unlocked and this
        function will return False.
        """
        if self.lock_timeout and (
            timezone.now() - self.lock_timeout > timedelta(minutes=5)
        ):
            self.unset_lock()
        return (
            self.lock_user
            and self.lock_timeout
            and (timezone.now() - self.lock_timeout < timedelta(minutes=5))
        )

    def set_lock(self, user):
        """Sets a lock on the current page or raise an AlreadyLocked exception."""
        if self.is_locked() and self.get_lock() != user:
            raise AlreadyLocked("The page is already locked by someone else")
        self.lock_user = user
        self.lock_timeout = timezone.now()
        super().save()

    def set_lock_recursive(self, user):
        """Locks recursively all the child pages for editing properties."""
        for p in self.children.all():
            p.set_lock_recursive(user)
        self.set_lock(user)

    def unset_lock_recursive(self):
        """Unlocks recursively all the child pages."""
        for p in self.children.all():
            p.unset_lock_recursive()
        self.unset_lock()

    def unset_lock(self):
        """Always try to unlock, even if there is no lock."""
        self.lock_user = None
        self.lock_timeout = None
        super().save()

    def get_lock(self):
        """Returns the page's mutex containing the time and the user in a dict."""
        if self.lock_user:
            return self.lock_user
        raise NotLocked("The page is not locked and thus can not return its user")

    def get_full_name(self):
        """Computes the real full_name of the page based on its name and its parent's name
        You can and must rely on this function when working on a page object that is not freshly fetched from the DB
        (For example when treating a Page object coming from a form).
        """
        if self.parent is None:
            return self.name
        return f"{self.parent.get_full_name()}/{self.name}"

    def get_display_name(self):
        rev = self.revisions.last()
        return rev.title if rev is not None else self.name

    @cached_property
    def is_club_page(self):
        club_root_page = Page.objects.filter(name=settings.SITH_CLUB_ROOT_PAGE).first()
        return club_root_page is not None and (
            self == club_root_page or club_root_page in self.get_parent_list()
        )

    @cached_property
    def need_club_redirection(self):
        return self.is_club_page and self.name != settings.SITH_CLUB_ROOT_PAGE

    def delete(self):
        self.unset_lock_recursive()
        self.set_lock_recursive(User.objects.get(id=0))
        for child in self.children.all():
            child.parent = self.parent
            child.save()
            child.unset_lock_recursive()
        super().delete()


class PageRev(models.Model):
    """True content of the page.

    Each page object has a revisions field that is a list of PageRev, ordered by date.
    my_page.revisions.last() gives the PageRev object that is the most up-to-date, and thus,
    is the real content of the page.
    The content is in PageRev.title and PageRev.content .
    """

    revision = models.IntegerField(_("revision"))
    title = models.CharField(_("page title"), max_length=255, blank=True)
    content = models.TextField(_("page content"), blank=True)
    date = models.DateTimeField(_("date"), auto_now=True)
    author = models.ForeignKey(User, related_name="page_rev", on_delete=models.CASCADE)
    page = models.ForeignKey(Page, related_name="revisions", on_delete=models.CASCADE)

    class Meta:
        ordering = ["date"]

    def __getattribute__(self, attr):
        if attr == "owner_group":
            return self.page.owner_group
        elif attr == "edit_groups":
            return self.page.edit_groups
        elif attr == "view_groups":
            return self.page.view_groups
        elif attr == "unset_lock":
            return self.page.unset_lock
        else:
            return object.__getattribute__(self, attr)

    def __str__(self):
        return str(self.__dict__)

    def save(self, *args, **kwargs):
        if self.revision is None:
            self.revision = self.page.revisions.all().count() + 1
        super().save(*args, **kwargs)
        # Don't forget to unlock, otherwise, people will have to wait for the page's timeout
        self.page.unset_lock()

    def get_absolute_url(self):
        return reverse("core:page", kwargs={"page_name": self.page._full_name})

    def can_be_edited_by(self, user):
        return self.page.can_be_edited_by(user)


class Notification(models.Model):
    user = models.ForeignKey(
        User, related_name="notifications", on_delete=models.CASCADE
    )
    url = models.CharField(_("url"), max_length=255)
    param = models.CharField(_("param"), max_length=128, default="")
    type = models.CharField(
        _("type"), max_length=32, choices=settings.SITH_NOTIFICATIONS, default="GENERIC"
    )
    date = models.DateTimeField(_("date"), default=timezone.now)
    viewed = models.BooleanField(_("viewed"), default=False, db_index=True)

    def __str__(self):
        if self.param:
            return self.get_type_display() % self.param
        return self.get_type_display()

    def save(self, *args, **kwargs):
        if not self.id and self.type in settings.SITH_PERMANENT_NOTIFICATIONS:
            old_notif = self.user.notifications.filter(type=self.type).last()
            if old_notif:
                old_notif.callback()
                old_notif.save()
                return
        super().save(*args, **kwargs)

    def callback(self):
        # Get the callback defined in settings to update existing
        # notifications
        mod_name, func_name = settings.SITH_PERMANENT_NOTIFICATIONS[self.type].rsplit(
            ".", 1
        )
        mod = importlib.import_module(mod_name)
        getattr(mod, func_name)(self)


class Gift(models.Model):
    label = models.CharField(_("label"), max_length=255)
    date = models.DateTimeField(_("date"), default=timezone.now)
    user = models.ForeignKey(User, related_name="gifts", on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.translated_label, self.date.strftime("%d %b %Y"))

    @property
    def translated_label(self):
        translations = [
            label[1] for label in settings.SITH_GIFT_LIST if label[0] == self.label
        ]
        if len(translations) > 0:
            return translations[0]
        return self.label

    def is_owned_by(self, user):
        if user.is_anonymous:
            return False
        return user.is_board_member or user.is_root


class OperationLog(models.Model):
    """General purpose log object to register operations."""

    date = models.DateTimeField(_("date"), auto_now_add=True)
    label = models.CharField(_("label"), max_length=255)
    operator = models.ForeignKey(
        User, related_name="logs", on_delete=models.SET_NULL, null=True
    )
    operation_type = models.CharField(
        _("operation type"), max_length=40, choices=settings.SITH_LOG_OPERATION_TYPE
    )

    def __str__(self):
        return "%s - %s - %s" % (self.operation_type, self.label, self.operator)

    def is_owned_by(self, user):
        return user.is_root
