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

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from club.models import Club
from core.models import User, RealGroup
from counter.models import Customer, Product, Selling, Counter, Refilling
from subscription.models import Subscription


class MergeUserTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("populate")
        cls.ae = Club.objects.get(unix_name="ae")
        cls.eboutic = Counter.objects.get(name="Eboutic")
        cls.barbar = Product.objects.get(code="BARB")
        cls.barbar.selling_price = 2
        cls.barbar.save()
        cls.root = User.objects.get(username="root")

    def setUp(self) -> None:
        super().setUp()
        self.to_keep = User(username="to_keep", password="plop", email="u.1@utbm.fr")
        self.to_delete = User(username="to_del", password="plop", email="u.2@utbm.fr")
        self.to_keep.save()
        self.to_delete.save()
        self.client.login(username="root", password="plop")

    def test_simple(self):
        self.to_delete.first_name = "Biggus"
        self.to_keep.last_name = "Dickus"
        self.to_keep.nick_name = "B'ian"
        self.to_keep.address = "Jerusalem"
        self.to_delete.parent_address = "Rome"
        self.to_delete.address = "Rome"
        subscribers = RealGroup.objects.get(name="Subscribers")
        mde_admin = RealGroup.objects.get(name="MDE admin")
        sas_admin = RealGroup.objects.get(name="SAS admin")
        self.to_keep.groups.add(subscribers.id)
        self.to_delete.groups.add(mde_admin.id)
        self.to_keep.groups.add(sas_admin.id)
        self.to_delete.groups.add(sas_admin.id)
        self.to_delete.save()
        self.to_keep.save()
        data = {"user1": self.to_keep.id, "user2": self.to_delete.id}
        res = self.client.post(reverse("rootplace:merge"), data)
        self.assertRedirects(res, self.to_keep.get_absolute_url())
        self.assertFalse(User.objects.filter(pk=self.to_delete.pk).exists())
        self.to_keep = User.objects.get(pk=self.to_keep.pk)
        # fields of to_delete should be assigned to to_keep
        # if they were not set beforehand
        self.assertEqual("Biggus", self.to_keep.first_name)
        self.assertEqual("Dickus", self.to_keep.last_name)
        self.assertEqual("B'ian", self.to_keep.nick_name)
        self.assertEqual("Jerusalem", self.to_keep.address)
        self.assertEqual("Rome", self.to_keep.parent_address)
        self.assertEqual(3, self.to_keep.groups.count())
        groups = list(self.to_keep.groups.all())
        expected = [subscribers, mde_admin, sas_admin]
        self.assertCountEqual(groups, expected)

    def test_both_subscribers_and_with_account(self):
        Customer(user=self.to_keep, account_id="11000l", amount=0).save()
        Customer(user=self.to_delete, account_id="12000m", amount=0).save()
        Refilling(
            amount=10,
            operator=self.root,
            customer=self.to_keep.customer,
            counter=self.eboutic,
        ).save()
        Refilling(
            amount=20,
            operator=self.root,
            customer=self.to_delete.customer,
            counter=self.eboutic,
        ).save()
        Selling(
            label="barbar",
            counter=self.eboutic,
            club=self.ae,
            product=self.barbar,
            customer=self.to_keep.customer,
            seller=self.root,
            unit_price=2,
            quantity=2,
            payment_method="SITH_ACCOUNT",
        ).save()
        Selling(
            label="barbar",
            counter=self.eboutic,
            club=self.ae,
            product=self.barbar,
            customer=self.to_delete.customer,
            seller=self.root,
            unit_price=2,
            quantity=4,
            payment_method="SITH_ACCOUNT",
        ).save()
        today = date.today()
        # both subscriptions began last month and shall end in 5 months
        Subscription(
            member=self.to_keep,
            subscription_type="un-semestre",
            payment_method="EBOUTIC",
            subscription_start=today - timedelta(30),
            subscription_end=today + timedelta(5 * 30),
        ).save()
        Subscription(
            member=self.to_delete,
            subscription_type="un-semestre",
            payment_method="EBOUTIC",
            subscription_start=today - timedelta(30),
            subscription_end=today + timedelta(5 * 30),
        ).save()
        data = {"user1": self.to_keep.id, "user2": self.to_delete.id}
        res = self.client.post(reverse("rootplace:merge"), data)
        self.to_keep = User.objects.get(pk=self.to_keep.id)
        self.assertRedirects(res, self.to_keep.get_absolute_url())
        # to_keep had 10€ at first and bought 2 barbar worth 2€ each
        # to_delete had 20€ and bought 4 barbar
        # total should be 10 - 4 + 20 - 8 = 18
        self.assertAlmostEqual(18, self.to_keep.customer.amount, delta=0.0001)
        self.assertEqual(2, self.to_keep.customer.buyings.count())
        self.assertEqual(2, self.to_keep.customer.refillings.count())
        self.assertTrue(self.to_keep.is_subscribed)
        # to_keep had 5 months of subscription remaining and received
        # 5 more months from to_delete, so he should be subscribed for 10 months
        self.assertEqual(
            today + timedelta(10 * 30),
            self.to_keep.subscriptions.order_by("subscription_end")
            .last()
            .subscription_end,
        )

    def test_godfathers(self):
        users = list(User.objects.all()[:4])
        self.to_keep.godfathers.add(users[0])
        self.to_keep.godchildren.add(users[1])
        self.to_delete.godfathers.add(users[2])
        self.to_delete.godfathers.add(self.to_keep)
        self.to_delete.godchildren.add(users[3])
        data = {"user1": self.to_keep.id, "user2": self.to_delete.id}
        res = self.client.post(reverse("rootplace:merge"), data)
        self.assertRedirects(res, self.to_keep.get_absolute_url())
        self.to_keep = User.objects.get(pk=self.to_keep.id)
        self.assertCountEqual(list(self.to_keep.godfathers.all()), [users[0], users[2]])
        self.assertCountEqual(
            list(self.to_keep.godchildren.all()), [users[1], users[3]]
        )

    def test_keep_has_no_account(self):
        Customer(user=self.to_delete, account_id="12000m", amount=0).save()
        Refilling(
            amount=20,
            operator=self.root,
            customer=self.to_delete.customer,
            counter=self.eboutic,
        ).save()
        Selling(
            label="barbar",
            counter=self.eboutic,
            club=self.ae,
            product=self.barbar,
            customer=self.to_delete.customer,
            seller=self.root,
            unit_price=2,
            quantity=4,
            payment_method="SITH_ACCOUNT",
        ).save()
        data = {"user1": self.to_keep.id, "user2": self.to_delete.id}
        res = self.client.post(reverse("rootplace:merge"), data)
        self.to_keep = User.objects.get(pk=self.to_keep.id)
        self.assertRedirects(res, self.to_keep.get_absolute_url())
        # to_delete had 20€ and bought 4 barbar worth 2€ each
        # total should be 20 - 8 = 12
        self.assertTrue(hasattr(self.to_keep, "customer"))
        self.assertAlmostEqual(12, self.to_keep.customer.amount, delta=0.0001)

    def test_delete_has_no_account(self):
        Customer(user=self.to_keep, account_id="12000m", amount=0).save()
        Refilling(
            amount=20,
            operator=self.root,
            customer=self.to_keep.customer,
            counter=self.eboutic,
        ).save()
        Selling(
            label="barbar",
            counter=self.eboutic,
            club=self.ae,
            product=self.barbar,
            customer=self.to_keep.customer,
            seller=self.root,
            unit_price=2,
            quantity=4,
            payment_method="SITH_ACCOUNT",
        ).save()
        data = {"user1": self.to_keep.id, "user2": self.to_delete.id}
        res = self.client.post(reverse("rootplace:merge"), data)
        self.to_keep = User.objects.get(pk=self.to_keep.id)
        self.assertRedirects(res, self.to_keep.get_absolute_url())
        # to_keep had 20€ and bought 4 barbar worth 2€ each
        # total should be 20 - 8 = 12
        self.assertTrue(hasattr(self.to_keep, "customer"))
        self.assertAlmostEqual(12, self.to_keep.customer.amount, delta=0.0001)
