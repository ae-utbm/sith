# Create your models here.
from datetime import timedelta

from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.utils import get_semester_code


class Timetable(models.Model):
    user = models.ForeignKey(User, verbose_name=_("user"), on_delete=models.CASCADE)
    semester = models.CharField(
        _("semester"),
        default=get_semester_code,
        validators=[RegexValidator(r"(A|P)\d{2}")],
        blank=True,
    )

    class Meta:
        verbose_name = _("timetable")
        verbose_name_plural = _("timetables")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "semester"), name="timetable_unique_user_semester"
            )
        ]
        permissions = [("add_self_timetable", "Can add its own timetable")]

    def __str__(self) -> str:
        return f"{self.user} {self.semester}"


class TimetableSlot(models.Model):
    MINUTES_PER_SLOT = 15

    class WeekDay(models.IntegerChoices):
        MONDAY = 1
        TUESDAY = 2
        WEDNESDAY = 3
        THURSDAY = 4
        FRIDAY = 5
        SATURDAY = 6
        SUNDAY = 7

    timetable = models.ForeignKey(
        Timetable,
        verbose_name=_("timetable"),
        related_name="slots",
        on_delete=models.CASCADE,
    )
    weekday = models.SmallIntegerField(_("weekday"), choices=WeekDay)
    # there are 4 * 24 = 96 quarters in a day, and we start counting at 0
    start_at = models.PositiveSmallIntegerField(
        _("start at"), validators=[MaxValueValidator(95)]
    )
    end_at = models.PositiveSmallIntegerField(
        _("end at"), validators=[MaxValueValidator(95)]
    )

    class Meta:
        verbose_name = _("timetable slot")
        verbose_name_plural = _("timetable slots")
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")),
                name="timetable_slot_end_after_start",
            )
        ]

    def __str__(self) -> str:
        return f"{self.start_hour} - {self.end_hour} - {self.get_weekday_display()}"

    @property
    def start_hour(self):
        return timedelta(minutes=self.start_at * self.MINUTES_PER_SLOT)

    @property
    def end_hour(self):
        return timedelta(minutes=self.end_at * self.MINUTES_PER_SLOT)
