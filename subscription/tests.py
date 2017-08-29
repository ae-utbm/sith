# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
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
from datetime import date
from unittest import mock

from django.test import TestCase
from subscription.models import Subscription

class FakeDate(date):
    """A fake replacement for date that can be mocked for testing."""
    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)

def date_mock_today(year, month, day):
    FakeDate.today = classmethod(lambda cls: date(year, month, day))

class SubscribtionTest(TestCase):

    @mock.patch('subscription.models.date', FakeDate)
    def test_start_dates_sliding_without_start(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_start(duration=1)
        self.assertTrue(d == date(2015, 9, 18))
        self.assertTrue(Subscription.compute_start(duration=2) == date(2015, 9, 18))

    def test_start_dates_sliding_with_start(self):
        self.assertTrue(Subscription.compute_start(date(2015, 5, 17), 1) ==
            date(2015, 5, 17))
        self.assertTrue(Subscription.compute_start(date(2015, 5, 17), 2) ==
            date(2015, 5, 17))

    @mock.patch('subscription.models.date', FakeDate)
    def test_start_dates_not_sliding_without_start(self):
        date_mock_today(2015, 5, 17)
        self.assertTrue(Subscription.compute_start(duration=3) == date(2015, 2, 15))
        date_mock_today(2016, 1, 18)
        self.assertTrue(Subscription.compute_start(duration=4) == date(2015, 8, 15))
        date_mock_today(2015, 9, 18)
        self.assertTrue(Subscription.compute_start(duration=4) == date(2015, 8, 15))

    def test_start_dates_not_sliding_with_start(self):
        self.assertTrue(Subscription.compute_start(date(2015, 5, 17), 3) ==
            date(2015, 2, 15))
        self.assertTrue(Subscription.compute_start(date(2015, 1, 11), 3) ==
            date(2014, 8, 15))

    @mock.patch('subscription.models.date', FakeDate)
    def test_end_dates_sliding(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_end(2)
        self.assertTrue(d == date(2016, 9, 18))
        d = Subscription.compute_end(1)
        self.assertTrue(d == date(2016, 3, 18))

    @mock.patch('subscription.models.date', FakeDate)
    def test_end_dates_not_sliding_without_start(self):
        date_mock_today(2015, 9, 18)
        d = Subscription.compute_end(duration=3)
        self.assertTrue(d == date(2017, 2, 15))
        d = Subscription.compute_end(duration=4)
        self.assertTrue(d == date(2017, 8, 15))

    def test_end_dates_not_sliding_with_start(self):
        d = Subscription.compute_end(duration=3, start=date(2015, 9, 18))
        self.assertTrue(d == date(2017, 3, 18))
        d = Subscription.compute_end(duration=4, start=date(2015, 9, 18))
        self.assertTrue(d == date(2017, 9, 18))

