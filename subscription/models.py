#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import math
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.utils import get_start_of_semester


def validate_type(value):
    if value not in settings.SITH_SUBSCRIPTIONS:
        raise ValidationError(_("Bad subscription type"))


def validate_payment(value):
    if value not in settings.SITH_SUBSCRIPTION_PAYMENT_METHOD:
        raise ValidationError(_("Bad payment method"))


class Subscription(models.Model):
    member = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    subscription_type = models.CharField(
        _("subscription type"),
        max_length=255,
        choices=(
            (k, v["name"]) for k, v in sorted(settings.SITH_SUBSCRIPTIONS.items())
        ),
    )
    subscription_start = models.DateField(_("subscription start"))
    subscription_end = models.DateField(_("subscription end"))
    payment_method = models.CharField(
        _("payment method"),
        max_length=255,
        choices=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD,
    )
    location = models.CharField(
        choices=settings.SITH_SUBSCRIPTION_LOCATIONS,
        max_length=20,
        verbose_name=_("location"),
    )

    class Meta:
        ordering = ["subscription_start"]

    def __str__(self):
        if hasattr(self, "member") and self.member is not None:
            return f"{self.member.username} - {self.pk}"
        else:
            return f"No user - {self.pk}"

    def save(self, *args, **kwargs) -> None:
        if self.member.was_subscribed:
            super().save()
            return

        from counter.models import Customer

        customer, _ = Customer.get_or_create(self.member)
        # Someone who subscribed once will be considered forever
        # as an old subscriber.
        self.member.groups.add(settings.SITH_GROUP_OLD_SUBSCRIBERS_ID)
        self.member.make_home()
        # now that the user is an old subscriber, change the cached
        # property accordingly
        self.member.__dict__["was_subscribed"] = True
        super().save()

    def get_absolute_url(self):
        return reverse("core:user_edit", kwargs={"user_id": self.member_id})

    def clean(self):
        if self.member._state.adding:
            # if the user is being created, then it makes no sense
            # to check if the user is already subscribed
            return
        today = localdate()
        threshold = timedelta(weeks=settings.SITH_SUBSCRIPTION_END)
        # a user may subscribe if :
        # - he/she is not currently subscribed
        # - its current subscription ends in less than a few weeks
        overlapping_subscriptions = Subscription.objects.exclude(pk=self.pk).filter(
            member=self.member,
            subscription_start__lte=today,
            subscription_end__gte=today + threshold,
        )
        if overlapping_subscriptions.exists():
            raise ValidationError(
                _("You can not subscribe many time for the same period")
            )

    @staticmethod
    def compute_start(
        d: date | None = None, duration: int | float = 1, user: User | None = None
    ) -> date:
        """Computes the start date of the subscription.

        The computation is done with respect to the given date (default is today)
        and the start date given in settings.SITH_SEMESTER_START_AUTUMN.
        It takes the nearest past start date.
        Exemples: with SITH_SEMESTER_START_AUTUMN = (8, 15)
            Today      -> Start date
            2015-03-17 -> 2015-02-15
            2015-01-11 -> 2014-08-15.
        """
        if not d:
            d = date.today()
        if user is not None and user.subscriptions.exists():
            last = user.subscriptions.last()
            if last.is_valid_now():
                d = last.subscription_end
        if duration <= 2:  # Sliding subscriptions for 1 or 2 semesters
            return d
        return get_start_of_semester(d)

    @staticmethod
    def compute_end(
        duration: int | float, start: date | None = None, user: User | None = None
    ) -> date:
        """Compute the end date of the subscription.

        Args:
            duration:
                the duration of the subscription, in semester
                (for example, 2 => 2 semesters => 1 year)
            start: The start date of the subscription
            user: the user which is (or will be) subscribed

        Exemples:
            Start - Duration -> End date
            2015-09-18 - 1 -> 2016-03-18
            2015-09-18 - 2 -> 2016-09-18
            2015-09-18 - 3 -> 2017-03-18
            2015-09-18 - 4 -> 2017-09-18.
        """
        if start is None:
            start = Subscription.compute_start(duration=duration, user=user)

        return start + relativedelta(
            months=round(6 * duration),
            days=math.ceil((6 * duration - round(6 * duration)) * 30),
        )

    def can_be_edited_by(self, user: User):
        return user.is_board_member or user.is_root

    def is_valid_now(self):
        return self.subscription_start <= date.today() <= self.subscription_end

    @property
    def semester_duration(self) -> float:
        """Duration of this subscription, in number of semester.

        Notes:
            The `Subscription` object doesn't have to actually exist
            in the database to access this property

        Examples:
            ```py
            subscription = Subscription(subscription_type="deux-semestres")
            assert subscription.semester_duration == 2.0
            ```
        """
        return settings.SITH_SUBSCRIPTIONS[self.subscription_type]["duration"]
