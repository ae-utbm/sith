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
from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth.models import make_password
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localdate, now
from freezegun import freeze_time
from model_bakery import baker

from club.models import Club, Membership
from core.baker_recipes import board_user, subscriber_user, very_old_subscriber_user
from core.models import BanGroup, User
from counter.baker_recipes import product_recipe
from counter.models import (
    Counter,
    Customer,
    Permanency,
    Product,
    Refilling,
    Selling,
)


class TestFullClickBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = subscriber_user.make()
        cls.barmen = subscriber_user.make(password=make_password("plop"))
        cls.board_admin = board_user.make(password=make_password("plop"))
        cls.club_admin = subscriber_user.make()
        cls.root = baker.make(User, is_superuser=True)
        cls.subscriber = subscriber_user.make()

        cls.counter = baker.make(Counter, type="BAR")
        cls.counter.sellers.add(cls.barmen, cls.board_admin)

        cls.other_counter = baker.make(Counter, type="BAR")
        cls.other_counter.sellers.add(cls.barmen)

        cls.yet_another_counter = baker.make(Counter, type="BAR")

        cls.customer_old_can_buy = subscriber_user.make()
        sub = cls.customer_old_can_buy.subscriptions.first()
        sub.subscription_end = localdate() - timedelta(days=89)
        sub.save()

        cls.customer_old_can_not_buy = very_old_subscriber_user.make()

        cls.customer_can_not_buy = baker.make(User)

        cls.club_counter = baker.make(Counter, type="OFFICE")
        baker.make(
            Membership,
            start_date=now() - timedelta(days=30),
            club=cls.club_counter.club,
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
            user=cls.club_admin,
        )

    def updated_amount(self, user: User) -> Decimal:
        user.refresh_from_db()
        user.customer.refresh_from_db()
        return user.customer.amount


class TestRefilling(TestFullClickBase):
    def login_in_bar(self, barmen: User | None = None):
        used_barman = barmen if barmen is not None else self.board_admin
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": used_barman.username, "password": "plop"},
        )

    def refill_user(
        self,
        user: User | Customer,
        counter: Counter,
        amount: int,
        client: Client | None = None,
    ) -> HttpResponse:
        used_client = client if client is not None else self.client
        return used_client.post(
            reverse(
                "counter:refilling_create",
                kwargs={"customer_id": user.pk},
            ),
            {
                "amount": str(amount),
                "payment_method": "CASH",
                "bank": "OTHER",
            },
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={"counter_id": counter.id, "user_id": user.pk},
            ),
        )

    def test_refilling_office_fail(self):
        self.client.force_login(self.club_admin)
        assert self.refill_user(self.customer, self.club_counter, 10).status_code == 403

        self.client.force_login(self.root)
        assert self.refill_user(self.customer, self.club_counter, 10).status_code == 403

        self.client.force_login(self.subscriber)
        assert self.refill_user(self.customer, self.club_counter, 10).status_code == 403

        assert self.updated_amount(self.customer) == 0

    def test_refilling_no_refer_fail(self):
        def refill():
            return self.client.post(
                reverse(
                    "counter:refilling_create",
                    kwargs={"customer_id": self.customer.pk},
                ),
                {
                    "amount": "10",
                    "payment_method": "CASH",
                    "bank": "OTHER",
                },
            )

        self.client.force_login(self.club_admin)
        assert refill()

        self.client.force_login(self.root)
        assert refill()

        self.client.force_login(self.subscriber)
        assert refill()

        assert self.updated_amount(self.customer) == 0

    def test_refilling_not_connected_fail(self):
        assert self.refill_user(self.customer, self.counter, 10).status_code == 403
        assert self.updated_amount(self.customer) == 0

    def test_refilling_counter_open_but_not_connected_fail(self):
        self.login_in_bar()
        client = Client()
        assert (
            self.refill_user(self.customer, self.counter, 10, client=client).status_code
            == 403
        )
        assert self.updated_amount(self.customer) == 0

    def test_refilling_counter_no_board_member(self):
        self.login_in_bar(barmen=self.barmen)
        assert self.refill_user(self.customer, self.counter, 10).status_code == 403
        assert self.updated_amount(self.customer) == 0

    def test_refilling_user_can_not_buy(self):
        self.login_in_bar(barmen=self.barmen)

        assert (
            self.refill_user(self.customer_can_not_buy, self.counter, 10).status_code
            == 404
        )
        assert (
            self.refill_user(
                self.customer_old_can_not_buy, self.counter, 10
            ).status_code
            == 404
        )

    def test_refilling_counter_success(self):
        self.login_in_bar()

        assert self.refill_user(self.customer, self.counter, 30).status_code == 302
        assert self.updated_amount(self.customer) == 30
        assert self.refill_user(self.customer, self.counter, 10.1).status_code == 302
        assert self.updated_amount(self.customer) == Decimal("40.1")

        assert (
            self.refill_user(self.customer_old_can_buy, self.counter, 1).status_code
            == 302
        )
        assert self.updated_amount(self.customer_old_can_buy) == 1


@dataclass
class BasketItem:
    id: int | None = None
    quantity: int | None = None

    def to_form(self, index: int) -> dict[str, str]:
        return {
            f"form-{index}-{key}": str(value)
            for key, value in asdict(self).items()
            if value is not None
        }


class TestCounterClick(TestFullClickBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.underage_customer = subscriber_user.make()
        cls.banned_counter_customer = subscriber_user.make()
        cls.banned_alcohol_customer = subscriber_user.make()

        cls.set_age(cls.customer, 20)
        cls.set_age(cls.barmen, 20)
        cls.set_age(cls.club_admin, 20)
        cls.set_age(cls.banned_alcohol_customer, 20)
        cls.set_age(cls.underage_customer, 17)

        cls.banned_alcohol_customer.ban_groups.add(
            BanGroup.objects.get(pk=settings.SITH_GROUP_BANNED_ALCOHOL_ID)
        )
        cls.banned_counter_customer.ban_groups.add(
            BanGroup.objects.get(pk=settings.SITH_GROUP_BANNED_COUNTER_ID)
        )

        cls.beer = product_recipe.make(
            limit_age=18, selling_price="1.5", special_selling_price="1"
        )
        cls.beer_tap = product_recipe.make(
            limit_age=18,
            tray=True,
            selling_price="1.5",
            special_selling_price="1",
        )

        cls.snack = product_recipe.make(
            limit_age=0, selling_price="1.5", special_selling_price="1"
        )
        cls.stamps = product_recipe.make(
            limit_age=0, selling_price="1.5", special_selling_price="1"
        )

        cls.counter.products.add(cls.beer, cls.beer_tap, cls.snack)

        cls.other_counter.products.add(cls.snack)

        cls.club_counter.products.add(cls.stamps)

    def login_in_bar(self, barmen: User | None = None):
        used_barman = barmen if barmen is not None else self.barmen
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": used_barman.username, "password": "plop"},
        )

    @classmethod
    def set_age(cls, user: User, age: int):
        user.date_of_birth = localdate().replace(year=localdate().year - age)
        user.save()

    def submit_basket(
        self,
        user: User,
        basket: list[BasketItem],
        counter: Counter | None = None,
        client: Client | None = None,
    ) -> HttpResponse:
        used_counter = counter if counter is not None else self.counter
        used_client = client if client is not None else self.client
        data = {
            "form-TOTAL_FORMS": str(len(basket)),
            "form-INITIAL_FORMS": "0",
        }
        for index, item in enumerate(basket):
            data.update(item.to_form(index))
        return used_client.post(
            reverse(
                "counter:click",
                kwargs={"counter_id": used_counter.id, "user_id": user.id},
            ),
            data,
        )

    def refill_user(self, user: User, amount: Decimal | int):
        baker.make(Refilling, amount=amount, customer=user.customer, is_validated=False)

    def test_click_eboutic_failure(self):
        eboutic = baker.make(Counter, type="EBOUTIC")
        self.client.force_login(self.club_admin)
        assert (
            self.submit_basket(
                self.customer,
                [BasketItem(self.stamps.id, 5)],
                counter=eboutic,
            ).status_code
            == 404
        )

    def test_click_office_success(self):
        self.refill_user(self.customer, 10)
        self.client.force_login(self.club_admin)

        assert (
            self.submit_basket(
                self.customer,
                [BasketItem(self.stamps.id, 5)],
                counter=self.club_counter,
            ).status_code
            == 302
        )
        assert self.updated_amount(self.customer) == Decimal("2.5")

        # Test no special price on office counter
        self.refill_user(self.club_admin, 10)

        assert (
            self.submit_basket(
                self.club_admin,
                [BasketItem(self.stamps.id, 1)],
                counter=self.club_counter,
            ).status_code
            == 302
        )

        assert self.updated_amount(self.club_admin) == Decimal("8.5")

    def test_click_bar_success(self):
        self.refill_user(self.customer, 10)
        self.login_in_bar(self.barmen)

        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.beer.id, 2),
                    BasketItem(self.snack.id, 1),
                ],
            ).status_code
            == 302
        )

        assert self.updated_amount(self.customer) == Decimal("5.5")

        # Test barmen special price

        self.refill_user(self.barmen, 10)

        assert (
            self.submit_basket(self.barmen, [BasketItem(self.beer.id, 1)])
        ).status_code == 302

        assert self.updated_amount(self.barmen) == Decimal("9")

    def test_click_tray_price(self):
        self.refill_user(self.customer, 20)
        self.login_in_bar(self.barmen)

        # Not applying tray price
        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.beer_tap.id, 2),
                ],
            ).status_code
            == 302
        )

        assert self.updated_amount(self.customer) == Decimal("17")

        # Applying tray price
        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.beer_tap.id, 7),
                ],
            ).status_code
            == 302
        )

        assert self.updated_amount(self.customer) == Decimal("8")

    def test_click_alcool_unauthorized(self):
        self.login_in_bar()

        for user in [self.underage_customer, self.banned_alcohol_customer]:
            self.refill_user(user, 10)

            # Buy product without age limit
            assert (
                self.submit_basket(
                    user,
                    [
                        BasketItem(self.snack.id, 2),
                    ],
                ).status_code
                == 302
            )

            assert self.updated_amount(user) == Decimal("7")

            # Buy product without age limit
            assert (
                self.submit_basket(
                    user,
                    [
                        BasketItem(self.beer.id, 2),
                    ],
                ).status_code
                == 200
            )

            assert self.updated_amount(user) == Decimal("7")

    def test_click_unauthorized_customer(self):
        self.login_in_bar()

        for user in [
            self.banned_counter_customer,
            self.customer_old_can_not_buy,
        ]:
            self.refill_user(user, 10)
            resp = self.submit_basket(
                user,
                [
                    BasketItem(self.snack.id, 2),
                ],
            )
            assert resp.status_code == 302
            assert resp.url == resolve_url(self.counter)

            assert self.updated_amount(user) == Decimal("10")

    def test_click_user_without_customer(self):
        self.login_in_bar()
        assert (
            self.submit_basket(
                self.customer_can_not_buy,
                [
                    BasketItem(self.snack.id, 2),
                ],
            ).status_code
            == 404
        )

    def test_click_allowed_old_subscriber(self):
        self.login_in_bar()
        self.refill_user(self.customer_old_can_buy, 10)
        assert (
            self.submit_basket(
                self.customer_old_can_buy,
                [
                    BasketItem(self.snack.id, 2),
                ],
            ).status_code
            == 302
        )

        assert self.updated_amount(self.customer_old_can_buy) == Decimal("7")

    def test_click_wrong_counter(self):
        self.login_in_bar()
        self.refill_user(self.customer, 10)
        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.snack.id, 2),
                ],
                counter=self.other_counter,
            ).status_code
            == 302  # Redirect to counter main
        )

        # We want to test sending requests from another counter while
        # we are currently registered to another counter
        # so we connect to a counter and
        # we create a new client, in order to check
        # that using a client not logged to a counter
        # where another client is logged still isn't authorized.
        client = Client()
        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.snack.id, 2),
                ],
                counter=self.counter,
                client=client,
            ).status_code
            == 302  # Redirect to counter main
        )

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_not_connected(self):
        self.refill_user(self.customer, 10)
        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.snack.id, 2),
                ],
            ).status_code
            == 302  # Redirect to counter main
        )

        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.snack.id, 2),
                ],
                counter=self.club_counter,
            ).status_code
            == 403
        )

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_product_not_in_counter(self):
        self.refill_user(self.customer, 10)
        self.login_in_bar()

        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.stamps.id, 2),
                ],
            ).status_code
            == 200
        )
        assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_product_invalid(self):
        self.refill_user(self.customer, 10)
        self.login_in_bar()

        for item in [
            BasketItem("-1", 2),
            BasketItem(self.beer.id, -1),
            BasketItem(None, 1),
            BasketItem(self.beer.id, None),
            BasketItem(None, None),
        ]:
            assert (
                self.submit_basket(
                    self.customer,
                    [item],
                ).status_code
                == 200
            )

            assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_not_enough_money(self):
        self.refill_user(self.customer, 10)
        self.login_in_bar()

        assert (
            self.submit_basket(
                self.customer,
                [
                    BasketItem(self.beer_tap.id, 5),
                    BasketItem(self.beer.id, 10),
                ],
            ).status_code
            == 200
        )

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_annotate_has_barman_queryset(self):
        """Test if the custom queryset method `annotate_has_barman` works as intended."""
        counters = Counter.objects.annotate_has_barman(self.barmen)
        for counter in counters:
            if counter in (self.counter, self.other_counter):
                assert counter.has_annotated_barman
            else:
                assert not counter.has_annotated_barman


class TestCounterStats(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counter = Counter.objects.get(id=2)
        cls.krophil = User.objects.get(username="krophil")
        cls.skia = User.objects.get(username="skia")
        cls.sli = User.objects.get(username="sli")
        cls.root = User.objects.get(username="root")
        cls.subscriber = User.objects.get(username="subscriber")
        cls.old_subscriber = User.objects.get(username="old_subscriber")
        cls.counter.sellers.add(cls.sli, cls.root, cls.skia, cls.krophil)

        barbar = Product.objects.get(code="BARB")

        # remove everything to make sure the fixtures bring no side effect
        Permanency.objects.all().delete()
        Selling.objects.all().delete()

        now = timezone.now()
        # total of sli : 5 hours
        Permanency.objects.create(
            user=cls.sli, start=now, end=now + timedelta(hours=1), counter=cls.counter
        )
        Permanency.objects.create(
            user=cls.sli,
            start=now + timedelta(hours=4),
            end=now + timedelta(hours=6),
            counter=cls.counter,
        )
        Permanency.objects.create(
            user=cls.sli,
            start=now + timedelta(hours=7),
            end=now + timedelta(hours=9),
            counter=cls.counter,
        )

        # total of skia : 16 days, 2 hours, 35 minutes and 54 seconds
        Permanency.objects.create(
            user=cls.skia, start=now, end=now + timedelta(hours=1), counter=cls.counter
        )
        Permanency.objects.create(
            user=cls.skia,
            start=now + timedelta(days=4, hours=1),
            end=now + timedelta(days=20, hours=2, minutes=35, seconds=54),
            counter=cls.counter,
        )

        # total of root : 1 hour + 20 hours (but the 20 hours were on last year)
        Permanency.objects.create(
            user=cls.root,
            start=now + timedelta(days=5),
            end=now + timedelta(days=5, hours=1),
            counter=cls.counter,
        )
        Permanency.objects.create(
            user=cls.root,
            start=now - timedelta(days=300, hours=20),
            end=now - timedelta(days=300),
            counter=cls.counter,
        )

        # total of krophil : 0 hour
        s = Selling(
            label=barbar.name,
            product=barbar,
            club=Club.objects.get(name=settings.SITH_MAIN_CLUB["name"]),
            counter=cls.counter,
            unit_price=2,
            seller=cls.skia,
        )

        krophil_customer = Customer.get_or_create(cls.krophil)[0]
        sli_customer = Customer.get_or_create(cls.sli)[0]
        skia_customer = Customer.get_or_create(cls.skia)[0]
        root_customer = Customer.get_or_create(cls.root)[0]

        # moderate drinker. Total : 100 €
        s.quantity = 50
        s.customer = krophil_customer
        s.save(allow_negative=True)

        # Sli is a drunkard. Total : 2000 €
        s.quantity = 100
        s.customer = sli_customer
        for _ in range(10):
            # little trick to make sure the instance is duplicated in db
            s.pk = None
            s.save(allow_negative=True)  # save ten different sales

        # Skia is a heavy drinker too. Total : 1000 €
        s.customer = skia_customer
        for _ in range(5):
            s.pk = None
            s.save(allow_negative=True)

        # Root is quite an abstemious one. Total : 2 €
        s.pk = None
        s.quantity = 1
        s.customer = root_customer
        s.save(allow_negative=True)

    def test_not_authenticated_user_fail(self):
        # Test with not login user
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 403

    def test_unauthorized_user_fails(self):
        self.client.force_login(User.objects.get(username="public"))
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 403

    def test_get_total_sales(self):
        """Test the result of the Counter.get_total_sales() method."""
        assert self.counter.get_total_sales() == 3102

    def test_top_barmen(self):
        """Test the result of Counter.get_top_barmen() is correct."""
        users = [self.skia, self.root, self.sli]
        perm_times = [
            timedelta(days=16, hours=2, minutes=35, seconds=54),
            timedelta(hours=21),
            timedelta(hours=5),
        ]
        assert list(self.counter.get_top_barmen()) == [
            {
                "user": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "promo": user.promo,
                "nickname": user.nick_name,
                "perm_sum": perm_time,
            }
            for user, perm_time in zip(users, perm_times)
        ]

    def test_top_customer(self):
        """Test the result of Counter.get_top_customers() is correct."""
        users = [self.sli, self.skia, self.krophil, self.root]
        sale_amounts = [2000, 1000, 100, 2]
        assert list(self.counter.get_top_customers()) == [
            {
                "user": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "promo": user.promo,
                "nickname": user.nick_name,
                "selling_sum": sale_amount,
            }
            for user, sale_amount in zip(users, sale_amounts)
        ]


class TestBarmanConnection(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.krophil = User.objects.get(username="krophil")
        cls.skia = User.objects.get(username="skia")
        cls.skia.customer.account = 800
        cls.krophil.customer.save()
        cls.skia.customer.save()

        cls.counter = Counter.objects.get(id=2)

    def test_barman_granted(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:details", args=[self.counter.id]))

        assert "<p>Entrez un code client : </p>" in str(response.content)

    def test_counters_list_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:activity", args=[self.counter.id]))

        assert '<li><a href="/user/10/">Kro Phil&#39;</a></li>' in str(response.content)

    def test_barman_denied(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "skia", "password": "plop"},
        )
        response_get = self.client.get(
            reverse("counter:details", args=[self.counter.id])
        )

        assert "<p>Merci de vous identifier</p>" in str(response_get.content)

    def test_counters_list_no_barmen(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": "krophil", "password": "plop"},
        )
        response = self.client.get(reverse("counter:activity", args=[self.counter.id]))

        assert '<li><a href="/user/1/">S&#39; Kia</a></li>' not in str(response.content)


@pytest.mark.django_db
def test_barman_timeout():
    """Test that barmen timeout is well managed."""
    bar = baker.make(Counter, type="BAR")
    user = baker.make(User)
    bar.sellers.add(user)
    baker.make(Permanency, counter=bar, user=user, start=now())

    qs = Counter.objects.annotate_is_open().filter(pk=bar.pk)

    bar = qs[0]
    assert bar.is_open
    assert bar.barmen_list == [user]
    qs.handle_timeout()  # handling timeout before the actual timeout should be no-op
    assert qs[0].is_open
    with freeze_time() as frozen_time:
        frozen_time.tick(timedelta(minutes=settings.SITH_BARMAN_TIMEOUT + 1))
        qs.handle_timeout()
        bar = qs[0]
        assert not bar.is_open
        assert bar.barmen_list == []


class TestClubCounterClickAccess(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counter = baker.make(Counter, type="OFFICE")
        cls.customer = subscriber_user.make()
        cls.counter_url = reverse(
            "counter:details", kwargs={"counter_id": cls.counter.id}
        )
        cls.click_url = reverse(
            "counter:click",
            kwargs={"counter_id": cls.counter.id, "user_id": cls.customer.id},
        )

        cls.user = subscriber_user.make()

    def setUp(self):
        cache.clear()

    def test_anonymous(self):
        res = self.client.get(self.click_url)
        assert res.status_code == 403

    def test_logged_in_without_rights(self):
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 403
        # being a member of the club, without being in the board, isn't enough
        baker.make(Membership, club=self.counter.club, user=self.user, role=1)
        res = self.client.get(self.click_url)
        assert res.status_code == 403

    def test_board_member(self):
        baker.make(Membership, club=self.counter.club, user=self.user, role=3)
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 200

    def test_barman(self):
        self.counter.sellers.add(self.user)
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 403
