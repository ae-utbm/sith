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

from typing import Iterable, Self

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator, validate_email
from django.db import ProgrammingError, models, transaction
from django.db.models import Exists, F, OuterRef, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel

from core.fields import ResizedImageField
from core.models import Group, Notification, Page, SithFile, User


class ClubQuerySet(models.QuerySet):
    def having_board_member(self, user: User) -> Self:
        """Filter all club in which the given user is a board member."""
        active_memberships = user.memberships.board().ongoing()
        return self.filter(Exists(active_memberships.filter(club=OuterRef("pk"))))


class Club(models.Model):
    """The Club class, made as a tree to allow nice tidy organization."""

    name = models.CharField(_("name"), unique=True, max_length=64)
    parent = models.ForeignKey(
        "Club", related_name="children", null=True, blank=True, on_delete=models.CASCADE
    )
    slug_name = models.SlugField(
        _("slug name"), max_length=30, unique=True, editable=False
    )
    logo = ResizedImageField(
        upload_to="club_logos",
        verbose_name=_("logo"),
        null=True,
        blank=True,
        force_format="WEBP",
        height=200,
        width=200,
    )
    is_active = models.BooleanField(_("is active"), default=True)
    short_description = models.CharField(
        _("short description"),
        max_length=1000,
        default="",
        blank=True,
        help_text=_(
            "A summary of what your club does. "
            "This will be displayed on the club list page."
        ),
    )
    address = models.CharField(_("address"), max_length=254)
    home = models.OneToOneField(
        SithFile,
        related_name="home_of_club",
        verbose_name=_("home"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    page = models.OneToOneField(
        Page, related_name="club", blank=True, on_delete=models.PROTECT
    )
    members_group = models.OneToOneField(
        Group, related_name="club", on_delete=models.PROTECT, editable=False
    )
    board_group = models.OneToOneField(
        Group, related_name="club_board", on_delete=models.PROTECT, editable=False
    )

    objects = ClubQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @transaction.atomic()
    def save(self, *args, **kwargs):
        creation = self._state.adding
        if (slug := slugify(self.name)[:30]) != self.slug_name:
            self.slug_name = slug
        if not creation:
            db_club = Club.objects.get(id=self.id)
            if self.name != db_club.name:
                self.home.name = self.slug_name
                self.home.save()
            if self.name != db_club.name:
                self.board_group.name = f"{self.name} - Bureau"
                self.board_group.save()
                self.members_group.name = f"{self.name} - Membres"
                self.members_group.save()
        if creation:
            self.board_group = Group.objects.create(
                name=f"{self.name} - Bureau", is_manually_manageable=False
            )
            self.members_group = Group.objects.create(
                name=f"{self.name} - Membres", is_manually_manageable=False
            )
            self.make_home()
        self.make_page()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("club:club_view", kwargs={"club_id": self.id})

    @cached_property
    def president(self) -> Membership | None:
        """Fetch the membership of the current president of this club."""
        return self.members.filter(end_date=None).order_by("role__order").first()

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

    def make_home(self) -> None:
        if self.home:
            return
        home_root = SithFile.objects.get(parent=None, name="clubs")
        root = User.objects.get(id=settings.SITH_ROOT_USER_ID)
        self.home = SithFile.objects.create(
            parent=home_root, name=self.slug_name, owner=root
        )

    def make_page(self) -> None:
        page_name = self.slug_name
        if not self.page_id:
            # Club.page is a OneToOneField, so if we are inside this condition
            # then self._meta.state.adding is True.
            club_root = Page.objects.get(name=settings.SITH_CLUB_ROOT_PAGE)
            public = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
            p = Page(name=page_name, parent=club_root)
            p.save(force_lock=True)
            p.view_groups.add(public)
            if self.parent and self.parent.page_id:
                p.parent_id = self.parent.page_id
            self.page = p
            return
        self.page.unset_lock()
        if self.page.name != page_name:
            self.page.name = page_name
        elif self.parent and self.parent.page and self.page.parent != self.parent.page:
            self.page.parent = self.parent.page
        self.page.save(force_lock=True)

    def create_default_roles(self):
        """Create some roles that should exist by default for this club.

        The created roles are : president, treasurer, active member and curious.

        Warnings:
            When calling this method, no club must exist yet for this club.
        """
        if self.roles.exists():
            raise ProgrammingError(
                "Default roles can be created only for clubs "
                "that don't have associated roles yet"
            )
        # The names are written in French, because there is no gettext involved
        # for strings stored in database, and the majority of users are french.
        roles = [
            ClubRole(name="Président⸱e", is_board=True, is_presidency=True),
            ClubRole(name="Trésorier⸱e", is_board=True, is_presidency=False),
            ClubRole(name="Membre actif⸱ve", is_board=False, is_presidency=False),
            ClubRole(
                name="Curieux⸱euse",
                description=(
                    "Les gens qui suivent l'activité "
                    "du club sans forcément y participer"
                ),
                is_board=False,
                is_presidency=False,
            ),
        ]
        for i, role in enumerate(roles):
            role.club = self
            role.order = i
        ClubRole.objects.bulk_create(roles)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        self.board_group.delete()
        self.members_group.delete()
        return super().delete(*args, **kwargs)

    def get_display_name(self) -> str:
        return self.name

    def is_owned_by(self, user: User) -> bool:
        """Method to see if that object can be super edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_root or user.is_board_member

    def get_full_logo_url(self) -> str:
        return f"https://{settings.SITH_URL}{self.logo.url}"

    def can_be_edited_by(self, user: User) -> bool:
        """Method to see if that object can be edited by the given user."""
        return self.has_rights_in_club(user)

    @cached_property
    def current_members(self) -> list[Membership]:
        return list(
            self.members.ongoing().select_related("user", "role").order_by("-role")
        )

    def get_membership_for(self, user: User) -> Membership | None:
        """Return the current membership of the given user."""
        if user.is_anonymous:
            return None
        return next((m for m in self.current_members if m.user_id == user.id), None)

    def has_rights_in_club(self, user: User) -> bool:
        return user.is_in_group(pk=self.board_group_id)


class ClubRole(OrderedModel):
    club = models.ForeignKey(
        Club,
        verbose_name=_("club"),
        help_text=_("The club with which this role is associated"),
        related_name="roles",
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("name"), max_length=50)
    description = models.TextField(_("description"), blank=True, default="")
    is_board = models.BooleanField(_("Board role"), default=False)
    is_presidency = models.BooleanField(_("Presidency role"), default=False)
    is_active = models.BooleanField(
        _("is active"),
        default=True,
        help_text=_(
            "If the role is inactive, people joining the club won't be able to get it."
        ),
    )

    order_with_respect_to = "club"

    class Meta(OrderedModel.Meta):
        verbose_name = _("club role")
        verbose_name_plural = _("club roles")
        constraints = [
            # presidency IMPLIES board <=> NOT presidency OR board
            # cf. MT1 :)
            models.CheckConstraint(
                condition=Q(is_presidency=False) | Q(is_board=True),
                name="clubrole_presidency_implies_board",
            )
        ]

    def __str__(self):
        return self.name

    def get_display_name(self):
        return f"{self.name} - {self.club.name}"

    def get_absolute_url(self):
        return reverse("club:club_roles", kwargs={"club_id": self.club_id})

    def clean(self):
        errors = []
        if self.is_presidency and not self.is_board:
            errors.append(
                ValidationError(
                    _(
                        "Role %(name)s was declared as a presidency role "
                        "without being a board role"
                    )
                    % {"name": self.name}
                )
            )
        roles = list(self.club.roles.all())
        if (
            self.is_board
            and self.order
            and any(r.order < self.order and not r.is_board for r in roles)
        ):
            errors.append(
                ValidationError(
                    _("Role %(role)s cannot be placed below a member role")
                    % {"role": self.name}
                )
            )
        if (
            self.is_presidency
            and self.order
            and any(r.order < self.order and not r.is_presidency for r in roles)
        ):
            errors.append(
                ValidationError(
                    _("Role %(role)s cannot be placed below a non-presidency role")
                    % {"role": self.name}
                )
            )
        if errors:
            raise ValidationError(errors)
        return super().clean()

    def save(self, *args, **kwargs):
        auto_order = self.order is None and self.is_board
        if not auto_order:
            super().save(*args, **kwargs)
            return
        # get the role that should be placed after the role we are dealing with.
        # So, if this is role is presidency, get the first board role ;
        # if it is a board role, get the first member role ;
        # and if it is a member role, get nothing (OrderedModel.save will
        # automatically put it in the last position anyway)
        filters = {"is_board": self.is_presidency, "is_presidency": False}
        next_role = self.club.roles.filter(**filters).order_by("order").first()
        super().save(*args, **kwargs)
        if next_role:
            self.above(next_role)


class MembershipQuerySet(models.QuerySet):
    def ongoing(self) -> Self:
        """Filter all memberships which are not finished yet."""
        return self.filter(Q(end_date=None) | Q(end_date__gt=localdate()))

    def board(self) -> Self:
        """Filter all memberships where the user is/was in the board.

        Be aware that users who were in the board in the past
        are included, even if there are no more members.

        If you want to get the users who are currently in the board,
        mind combining this with the [MembershipQuerySet.ongoing][]
        queryset method
        """
        return self.filter(role__is_board=True)

    def editable_by(self, user: User) -> Self:
        """Filter Memberships that this user can edit.

        Users with the `club.change_membership` permission can edit all Membership.
        The other users can edit :
        - their own membership
        - if they are board members, ongoing memberships with a role lower than their own

        For example, let's suppose the following users :
        - A : board member
        - B : board member
        - C : simple member
        - D : curious
        - E : old member

        A will be able to edit the memberships of A, C and D ;
        C and D will be able to edit only their own membership ;
        nobody will be able to edit E's membership.
        """
        if user.has_perm("club.change_membership"):
            return self.all()
        return self.ongoing().filter(
            Q(user=user)
            | Exists(
                Membership.objects.ongoing().filter(
                    user=user,
                    club=OuterRef("club"),
                    role__is_board=True,
                    role__order__lt=OuterRef("role__order"),
                )
            )
        )

    def update(self, **kwargs) -> int:
        """Remove users from club groups they are no more in
        and add them in the club groups they should be in.

        Be aware that this adds three db queries :

        - one to retrieve the updated memberships
        - one to perform group removal
        - and one to perform group attribution.
        """
        nb_rows = super().update(**kwargs)
        if nb_rows == 0:
            # if no row was affected, no need to edit club groups
            return 0

        memberships = set(self.select_related("club"))
        # delete all User-Group relations and recreate the necessary ones
        Membership._remove_club_groups(memberships)
        Membership._add_club_groups(memberships)
        return nb_rows

    def delete(self) -> tuple[int, dict[str, int]]:
        """Work just like the default Django's delete() method,
        but also remove the concerned users from the club groups.

        Be aware that this adds some db queries :

        - 1 to retrieve the deleted elements in order to perform
          post-delete operations.
          As we can't know if a delete will affect rows or not,
          this query will always happen
        - 1 query to remove the users from the club groups.
          If the delete operation affected no row,
          this query won't happen.
        """
        memberships = set(self.all())
        nb_rows, rows_counts = super().delete()
        if nb_rows > 0:
            Membership._remove_club_groups(memberships)
        return nb_rows, rows_counts


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
        on_delete=models.CASCADE,
    )
    club = models.ForeignKey(
        Club,
        verbose_name=_("club"),
        related_name="members",
        on_delete=models.CASCADE,
    )
    start_date = models.DateField(_("start date"), default=timezone.now)
    end_date = models.DateField(_("end date"), null=True, blank=True)
    role = models.ForeignKey(
        ClubRole,
        verbose_name=_("role"),
        related_name="members",
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        _("description"), max_length=128, null=False, blank=True
    )

    objects = MembershipQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")), name="end_after_start"
            ),
        ]

    def __str__(self):
        return (
            f"{self.club.name} - {self.user.username} "
            f"- {self.role.name} "
            f"- {str(_('past member')) if self.end_date is not None else ''}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # a save may either be an update or a creation
        # and may result in either an ongoing or an ended membership.
        # It could also be a retrogradation from the board to being a simple member.
        # To avoid problems, the user is removed from the club groups beforehand ;
        # he will be added back if necessary
        self._remove_club_groups([self])
        if self.end_date is None:
            self._add_club_groups([self])

    def get_absolute_url(self):
        return reverse("club:club_members", kwargs={"club_id": self.club_id})

    def is_owned_by(self, user: User) -> bool:
        """Method to see if that object can be super edited by the given user."""
        if user.is_anonymous:
            return False
        return user.is_root or user.is_board_member

    def can_be_edited_by(self, user: User) -> bool:
        """Check if that object can be edited by the given user."""
        if user.is_root or user.is_board_member:
            return True
        membership = self.club.get_membership_for(user)
        if not membership:
            return False
        return membership.user_id == user.id or (
            membership.is_board and membership.role.order < self.role.order
        )

    def delete(self, *args, **kwargs):
        self._remove_club_groups([self])
        super().delete(*args, **kwargs)

    @staticmethod
    def _remove_club_groups(
        memberships: Iterable[Membership],
    ) -> tuple[int, dict[str, int]]:
        """Remove users of those memberships from the club groups.

        For example, if a user is in the Troll club board,
        he is in the board group and the members group of the Troll.
        After calling this function, he will be in neither.

        Returns:
            The result of the deletion queryset.

        Warnings:
            If this function isn't used in combination
            with an actual deletion of the memberships,
            it will result in an inconsistent state,
            where users will be in the clubs, without
            having the associated rights.
        """
        clubs = {m.club_id for m in memberships}
        users = {m.user_id for m in memberships}
        groups = Group.objects.filter(Q(club__in=clubs) | Q(club_board__in=clubs))
        return User.groups.through.objects.filter(
            Q(group__in=groups) & Q(user__in=users)
        ).delete()

    @staticmethod
    def _add_club_groups(
        memberships: Iterable[Membership],
    ) -> list[User.groups.through]:
        """Add users of those memberships to the club groups.

        For example, if a user just joined the Troll club board,
        he will be added in both the members group and the board group
        of the club.

        Returns:
            The created User-Group relations.

        Warnings:
            If this function isn't used in combination
            with an actual update/creation of the memberships,
            it will result in an inconsistent state,
            where users will have the rights associated to the
            club, without actually being part of it.
        """
        # only active membership (i.e. `end_date=None`)
        # grant the attribution of club groups.
        memberships = [m for m in memberships if m.end_date is None]
        if not memberships:
            return []

        if sum(1 for m in memberships if not hasattr(m, "club")) > 1:
            # if more than one membership hasn't its `club` attribute set
            # it's less expensive to reload the whole query with
            # a select_related than perform a distinct query
            # to fetch each club.
            ids = {m.id for m in memberships}
            memberships = list(
                Membership.objects.filter(id__in=ids).select_related("club")
            )
        club_groups = []
        for membership in memberships:
            club_groups.append(
                User.groups.through(
                    user_id=membership.user_id,
                    group_id=membership.club.members_group_id,
                )
            )
            if membership.role.is_board:
                club_groups.append(
                    User.groups.through(
                        user_id=membership.user_id,
                        group_id=membership.club.board_group_id,
                    )
                )
        return User.groups.through.objects.bulk_create(
            club_groups, ignore_conflicts=True
        )


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
            unread_notif_subquery = Notification.objects.filter(
                user=OuterRef("pk"), type="MAILING_MODERATION", viewed=False
            )
            for user in User.objects.filter(
                ~Exists(unread_notif_subquery),
                groups__id__in=[settings.SITH_GROUP_COM_ADMIN_ID],
            ):
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
