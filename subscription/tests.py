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
from datetime import date
from unittest import mock

from django.test import TestCase
from subscription.models import Subscription
from core.models import User
from django.conf import settings
from datetime import datetime
from django.core.management import call_command


class FakeDate(date):
    """A fake replacement for date that can be mocked for testing."""

    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)


def date_mock_today(year, month, day):
    FakeDate.today = classmethod(lambda cls: date(year, month, day))


class SubscriptionUnitTest(TestCase):
    @mock.patch("subscription.models.date", FakeDate)
    def test_start_dates_sliding_without_start(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_start(duration=1)
        self.assertTrue(d == date(2015, 9, 18))
        self.assertTrue(Subscription.compute_start(duration=2) == date(2015, 9, 18))

    def test_start_dates_sliding_with_start(self):
        self.assertTrue(
            Subscription.compute_start(date(2015, 5, 17), 1) == date(2015, 5, 17)
        )
        self.assertTrue(
            Subscription.compute_start(date(2015, 5, 17), 2) == date(2015, 5, 17)
        )

    @mock.patch("subscription.models.date", FakeDate)
    def test_start_dates_not_sliding_without_start(self):
        date_mock_today(2015, 5, 17)
        self.assertTrue(Subscription.compute_start(duration=3) == date(2015, 2, 15))
        date_mock_today(2016, 1, 18)
        self.assertTrue(Subscription.compute_start(duration=4) == date(2015, 8, 15))
        date_mock_today(2015, 9, 18)
        self.assertTrue(Subscription.compute_start(duration=4) == date(2015, 8, 15))

    def test_start_dates_not_sliding_with_start(self):
        self.assertTrue(
            Subscription.compute_start(date(2015, 5, 17), 3) == date(2015, 2, 15)
        )
        self.assertTrue(
            Subscription.compute_start(date(2015, 1, 11), 3) == date(2014, 8, 15)
        )

    @mock.patch("subscription.models.date", FakeDate)
    def test_end_dates_sliding(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_end(2)
        self.assertTrue(d == date(2016, 9, 18))
        d = Subscription.compute_end(1)
        self.assertTrue(d == date(2016, 3, 18))

    @mock.patch("subscription.models.date", FakeDate)
    def test_end_dates_not_sliding_without_start(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_end(duration=3)
        self.assertTrue(d == date(2017, 2, 15))
        d = Subscription.compute_end(duration=4)
        self.assertTrue(d == date(2017, 8, 15))

    @mock.patch("subscription.models.date", FakeDate)
    def test_end_dates_with_float(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_end(duration=0.33)
        self.assertTrue(d == date(2015, 11, 18))
        d = Subscription.compute_end(duration=0.67)
        self.assertTrue(d == date(2016, 1, 19))
        d = Subscription.compute_end(duration=0.5)
        self.assertTrue(d == date(2015, 12, 18))

    def test_end_dates_not_sliding_with_start(self):
        d = Subscription.compute_end(duration=3, start=date(2015, 9, 18))
        self.assertTrue(d == date(2017, 3, 18))
        d = Subscription.compute_end(duration=4, start=date(2015, 9, 18))
        self.assertTrue(d == date(2017, 9, 18))


class SubscriptionIntegrationTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.user = User.objects.filter(username="public").first()

    def test_duration_one_month(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.166, start=s.subscription_start)
        s.save()
        self.assertTrue(s.subscription_end == date(2017, 9, 29))

    def test_duration_two_months(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.333, start=s.subscription_start)
        s.save()
        self.assertTrue(s.subscription_end == date(2017, 10, 29))

    def test_duration_one_day(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS["un-jour"]["duration"],
            start=s.subscription_start,
        )
        s.save()
        self.assertTrue(s.subscription_end == date(2017, 8, 30))

    def test_duration_three_months(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.5, start=s.subscription_start)
        s.save()
        self.assertTrue(s.subscription_end == date(2017, 11, 29))

    def test_duration_four_months(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2017, 8, 29)
        s.subscription_end = s.compute_end(duration=0.67, start=s.subscription_start)
        s.save()
        self.assertTrue(s.subscription_end == date(2017, 12, 30))

    def test_duration_six_weeks(self):

        s = Subscription(
            member=User.objects.filter(pk=self.user.pk).first(),
            subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[3],
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0],
        )
        s.subscription_start = date(2018, 9, 1)
        s.subscription_end = s.compute_end(duration=0.23, start=s.subscription_start)
        s.save()
        self.assertTrue(s.subscription_end == date(2018, 10, 13))

    @mock.patch("subscription.models.date", FakeDate)
    def test_dates_sliding_with_subscribed_user(self):
        user = User.objects.filter(pk=self.user.pk).first()
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
        self.assertTrue(s.subscription_end == date(2016, 8, 29))
        date_mock_today(2016, 8, 25)
        d = Subscription.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
            user=user,
        )

        self.assertTrue(d == date(2017, 8, 29))

    @mock.patch("subscription.models.date", FakeDate)
    def test_dates_renewal_sliding_during_two_free_monthes(self):
        user = User.objects.filter(pk=self.user.pk).first()
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
        self.assertTrue(s.subscription_end == date(2015, 10, 29))
        date_mock_today(2015, 9, 25)
        d = Subscription.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
            user=user,
        )
        self.assertTrue(d == date(2016, 10, 29))

    @mock.patch("subscription.models.date", FakeDate)
    def test_dates_renewal_sliding_after_two_free_monthes(self):
        user = User.objects.filter(pk=self.user.pk).first()
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
        self.assertTrue(s.subscription_end == date(2015, 10, 29))
        date_mock_today(2015, 11, 5)
        d = Subscription.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS["deux-semestres"]["duration"],
            user=user,
        )
        self.assertTrue(d == date(2016, 11, 5))
