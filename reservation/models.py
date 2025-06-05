from __future__ import annotations

from typing import Self

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
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


class ReservationSlotQuerySet(models.QuerySet):
    def overlapping_with(self, other: ReservationSlot) -> Self:
        return self.filter(
            Q(end_at__gt=other.start_at, end_ad__lt=other.end_at)
            | Q(start_at__lt=other.start_at, start_ad__gt=other.start_at)
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
    duration = models.DurationField(_("duration"))
    end_at = models.GeneratedField(
        verbose_name=_("slot end"),
        expression=F("start_at") + F("duration"),
        output_field=models.DateTimeField(),
        db_persist=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReservationSlotQuerySet.as_manager()

    class Meta:
        verbose_name = _("reservation slot")
        verbose_name_plural = _("reservation slots")

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
