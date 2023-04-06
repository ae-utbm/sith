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
from datetime import date

import freezegun
import pytest
from django.conf import settings
from django.test import TestCase

from core.models import User
from subscription.models import Subscription


@pytest.mark.parametrize(
    ("today", "duration", "expected_start"),
    [
        (date(2020, 9, 18), 1, date(2020, 9, 18)),
        (date(2020, 9, 18), 2, date(2020, 9, 18)),
        (date(2020, 5, 17), 3, date(2020, 2, 15)),
        (date(2021, 1, 18), 4, date(2020, 8, 15)),
        (date(2020, 9, 18), 4, date(2020, 8, 15)),
    ],
)
def test_subscription_compute_start_from_today(today, duration, expected_start):
    with freezegun.freeze_time(today):
        assert Subscription.compute_start(duration=duration) == expected_start


@pytest.mark.parametrize(
    ("start_date", "duration", "expected_start"),
    [
        (date(2020, 5, 17), 1, date(2020, 5, 17)),
        (date(2020, 5, 17), 2, date(2020, 5, 17)),
        (date(2020, 5, 17), 3, date(2020, 2, 15)),
        (date(2020, 1, 11), 3, date(2019, 8, 15)),
    ],
)
def test_subscription_compute_start_explicit(start_date, duration, expected_start):
    assert Subscription.compute_start(start_date, duration=duration) == expected_start


@pytest.mark.parametrize(
    ("today", "duration", "expected_end"),
    [
        (date(2020, 9, 18), 1, date(2021, 3, 18)),
        (date(2020, 9, 18), 2, date(2021, 9, 18)),
        (date(2020, 9, 18), 3, date(2022, 2, 15)),
        (date(2020, 5, 17), 4, date(2022, 8, 15)),
        (date(2020, 9, 18), 0.33, date(2020, 11, 18)),
        (date(2020, 9, 18), 0.67, date(2021, 1, 19)),
        (date(2020, 9, 18), 0.5, date(2020, 12, 18)),
    ],
)
def test_subscription_compute_end_from_today(today, duration, expected_end):
    with freezegun.freeze_time(today):
        assert Subscription.compute_end(duration=duration) == expected_end


@pytest.mark.parametrize(
    ("start_date", "duration", "expected_end"),
    [
        (date(2020, 9, 18), 3, date(2022, 3, 18)),
        (date(2020, 9, 18), 4, date(2022, 9, 18)),
    ],
)
def test_subscription_compute_end_from_today(start_date, duration, expected_end):
    assert Subscription.compute_end(duration, start_date) == expected_end


class SubscriptionIntegrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username="public")

    def test_duration_one_month(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.166, start=s.subscription_start)
        s.save()
        assert s.subscription_end == date(2017, 9, 29)

    def test_duration_two_months(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.333, start=s.subscription_start)
        s.save()
        assert s.subscription_end == date(2017, 10, 29)

    def test_duration_one_day(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS["un-jour"]["duration"],
            start=s.subscription_start,
        )
        s.save()
        assert s.subscription_end == date(2017, 8, 30)

    def test_duration_three_months(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.5, start=s.subscription_start)
        s.save()
        assert s.subscription_end == date(2017, 11, 29)

    def test_duration_four_months(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.67, start=s.subscription_start)
        s.save()
        assert s.subscription_end == date(2017, 12, 30)

    def test_duration_six_weeks(self):
        s = Subscription(
            member=self.user,
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2018, 9, 1)
        s.subscription_end = s.compute_end(duration=0.23, start=s.subscription_start)
        s.save()
        assert s.subscription_end == date(2018, 10, 13)

    def test_dates_sliding_with_subscribed_user(self):
        user = self.user
        s = Subscription(
            member=user,
            subscription_type="deux-semestres",
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2015, 8, 29)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
            start=s.subscription_start,
        )
        s.save()
        assert s.subscription_end == date(2016, 8, 29)
        with freezegun.freeze_time("2016-08-25"):
            d = Subscription.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
                user=user,
            )
            assert d == date(2017, 8, 29)

    def test_dates_renewal_sliding_during_two_free_monthes(self):
        user = self.user
        s = Subscription(
            member=user,
            subscription_type="deux-mois-essai",
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2015, 8, 29)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
            start=s.subscription_start,
        )
        s.save()
        assert s.subscription_end == date(2015, 10, 29)
        with freezegun.freeze_time("2015-09-25"):
            d = Subscription.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
                user=user,
            )
            assert d == date(2016, 10, 29)

    def test_dates_renewal_sliding_after_two_free_monthes(self):
        user = self.user
        s = Subscription(
            member=user,
            subscription_type="deux-mois-essai",
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2015, 8, 29)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
            start=s.subscription_start,
        )
        s.save()
        assert s.subscription_end == date(2015, 10, 29)
        with freezegun.freeze_time("2015-11-05"):
            d = Subscription.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
                user=user,
            )
            assert d == date(2016, 11, 5)
