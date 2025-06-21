from __future__ import annotations

from typing import Self

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from club.models import Club
from core.fields import ResizedImageField
from core.models import User


class Room(models.Model):
    name = models.CharField(_("room name"), max_length=100)
    description = models.TextField(_("description"), blank=True, default="")
    logo = ResizedImageField(
        width=100,
        height=100,
        force_format="WEBP",
        upload_to="rooms",
        verbose_name=_("logo"),
        blank=True,
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="reservable_rooms",
        verbose_name=_("room owner"),
        help_text=_("The club which manages this room"),
    )
    location = models.CharField(
        _("site"),
        blank=True,
        choices=[
            ("BELFORT", "Belfort"),
            ("SEVENANS", "Sévenans"),
            ("MONTBELIARD", "Montbéliard"),
        ],
    )

    class Meta:
        verbose_name = _("reservable room")
        verbose_name_plural = _("reservable rooms")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("reservation:room_detail", kwargs={"room_id": self.id})

    def can_be_edited_by(self, user: User) -> bool:
        # a user may edit a room if it has the global perm
        # or is in the owner club board
        return user.has_perm("reservation.change_room") or self.club.board_group_id in [
            g.id for g in user.cached_groups
        ]


class ReservationSlotQuerySet(models.QuerySet):
    def overlapping_with(self, other: ReservationSlot) -> Self:
        return self.filter(
            Q(end_at__gt=other.start_at, end_at__lt=other.end_at)
            | Q(start_at__lt=other.start_at, start_at__gt=other.start_at)
        )


class ReservationSlot(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("reserved room"),
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("author"))
    nb_people = models.PositiveSmallIntegerField(
        verbose_name=_("number of people"),
        help_text=_("How many people will attend this reservation slot"),
        default=1,
        validators=[MinValueValidator(1)],
    )
    comment = models.TextField(_("comment"), blank=True, default="")
    start_at = models.DateTimeField(_("slot start"), db_index=True)
    end_at = models.DateTimeField(verbose_name=_("slot end"))
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReservationSlotQuerySet.as_manager()

    class Meta:
        verbose_name = _("reservation slot")
        verbose_name_plural = _("reservation slots")
        constraints = [
            models.CheckConstraint(
                check=Q(end_at__gt=F("start_at")),
                name="reservation_slot_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.room.name} : {self.start_at} - {self.end_at}"

    def clean(self):
        super().clean()
        if (
            ReservationSlot.objects.overlapping_with(self)
            .filter(room_id=self.room_id)
            .exists()
        ):
            raise ValidationError(_("There is already a reservation on this slot."))
