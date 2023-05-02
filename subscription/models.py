# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from datetime import date, timedelta
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.forms import PasswordResetForm

from dateutil.relativedelta import relativedelta

import math

from core.models import User
from core.utils import get_start_of_semester


def validate_type(value):
    if value not in settings.SITH_SUBSCRIPTIONS.keys():
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

    def clean(self):
        try:
            for s in (
                Subscription.objects.filter(member=self.member)
                .exclude(pk=self.pk)
                .all()
            ):
                if (
                    s.is_valid_now()
                    and s.subscription_end
                    - timedelta(weeks=settings.SITH_SUBSCRIPTION_END)
                    > date.today()
                ):
                    raise ValidationError(
                        _("You can not subscribe many time for the same period")
                    )
        except:  # This should not happen, because the form should have handled the data before, but sadly, it still
            # calls the model validation :'(
            # TODO see SubscriptionForm's clean method
            raise ValidationError(_("Subscription error"))

    def save(self, *args, **kwargs):
        super(Subscription, self).save()
        from counter.models import Customer

        _, created = Customer.get_or_create(self.member)
        if created:
            form = PasswordResetForm({"email": self.member.email})
            if form.is_valid():
                form.save(
                    use_https=True,
                    email_template_name="core/new_user_email.jinja",
                    subject_template_name="core/new_user_email_subject.jinja",
                    from_email="ae@utbm.fr",
                )
        self.member.make_home()

    def get_absolute_url(self):
        return reverse("core:user_edit", kwargs={"user_id": self.member.pk})

    def __str__(self):
        if hasattr(self, "member") and self.member is not None:
            return self.member.username + " - " + str(self.pk)
        else:
            return "No user - " + str(self.pk)

    @staticmethod
    def compute_start(d=None, duration=1, user=None):
        """
        This function computes the start date of the subscription with respect to the given date (default is today),
        and the start date given in settings.SITH_START_DATE.
        It takes the nearest past start date.
        Exemples: with SITH_START_DATE = (8, 15)
            Today      -> Start date
            2015-03-17 -> 2015-02-15
            2015-01-11 -> 2014-08-15
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
    def compute_end(duration, start=None, user=None):
        """
        This function compute the end date of the subscription given a start date and a duration in number of semestre
        Exemple:
            Start - Duration -> End date
            2015-09-18 - 1 -> 2016-03-18
            2015-09-18 - 2 -> 2016-09-18
            2015-09-18 - 3 -> 2017-03-18
            2015-09-18 - 4 -> 2017-09-18
        """
        if start is None:
            start = Subscription.compute_start(duration=duration, user=user)

        return start + relativedelta(
            months=round(6 * duration),
            days=math.ceil((6 * duration - round(6 * duration)) * 30),
        )

    def can_be_edited_by(self, user):
        return user.is_board_member or user.is_root

    def is_valid_now(self):
        return self.subscription_start <= date.today() <= self.subscription_end
