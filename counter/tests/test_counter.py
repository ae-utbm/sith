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
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import Permission, make_password
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localdate, now
from freezegun import freeze_time
from model_bakery import baker
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertRedirects

from club.models import Membership
from core.baker_recipes import board_user, subscriber_user, very_old_subscriber_user
from core.models import BanGroup, User
from counter.baker_recipes import product_recipe, sale_recipe
from counter.models import (
    Counter,
    Customer,
    Permanency,
    Product,
    Refilling,
    ReturnableProduct,
    Selling,
)


def set_age(user: User, age: int):
    user.date_of_birth = localdate().replace(year=localdate().year - age)
    user.save()


def force_refill_user(user: User, amount: Decimal | int):
    baker.make(Refilling, amount=amount, customer=user.customer, is_validated=False)


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
        amount: int | float,
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

        set_age(cls.customer, 20)
        set_age(cls.barmen, 20)
        set_age(cls.club_admin, 20)
        set_age(cls.banned_alcohol_customer, 20)
        set_age(cls.underage_customer, 17)

        cls.banned_alcohol_customer.ban_groups.add(
            BanGroup.objects.get(pk=settings.SITH_GROUP_BANNED_ALCOHOL_ID)
        )
        cls.banned_counter_customer.ban_groups.add(
            BanGroup.objects.get(pk=settings.SITH_GROUP_BANNED_COUNTER_ID)
        )

        cls.gift = product_recipe.make(
            selling_price="-1.5",
            special_selling_price="-1.5",
        )
        cls.beer = product_recipe.make(
            limit_age=18, selling_price=1.5, special_selling_price=1
        )
        cls.beer_tap = product_recipe.make(
            limit_age=18, tray=True, selling_price=1.5, special_selling_price=1
        )
        cls.snack = product_recipe.make(
            limit_age=0, selling_price=1.5, special_selling_price=1
        )
        cls.stamps = product_recipe.make(
            limit_age=0, selling_price=1.5, special_selling_price=1
        )
        ReturnableProduct.objects.all().delete()
        cls.cons = baker.make(Product, selling_price=1)
        cls.dcons = baker.make(Product, selling_price=-1)
        baker.make(
            ReturnableProduct,
            product=cls.cons,
            returned_product=cls.dcons,
            max_return=3,
        )

        cls.counter.products.add(
            cls.gift, cls.beer, cls.beer_tap, cls.snack, cls.cons, cls.dcons
        )
        cls.other_counter.products.add(cls.snack)
        cls.club_counter.products.add(cls.stamps)

    def login_in_bar(self, barmen: User | None = None):
        used_barman = barmen if barmen is not None else self.barmen
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": used_barman.username, "password": "plop"},
        )

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

    def test_click_eboutic_failure(self):
        eboutic = baker.make(Counter, type="EBOUTIC")
        self.client.force_login(self.club_admin)
        res = self.submit_basket(
            self.customer, [BasketItem(self.stamps.id, 5)], counter=eboutic
        )
        assert res.status_code == 404

    def test_click_office_success(self):
        force_refill_user(self.customer, 10)
        self.client.force_login(self.club_admin)
        res = self.submit_basket(
            self.customer, [BasketItem(self.stamps.id, 5)], counter=self.club_counter
        )
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == Decimal("2.5")

        # Test no special price on office counter
        force_refill_user(self.club_admin, 10)
        res = self.submit_basket(
            self.club_admin, [BasketItem(self.stamps.id, 1)], counter=self.club_counter
        )
        assert res.status_code == 302

        assert self.updated_amount(self.club_admin) == Decimal("8.5")

    def test_click_bar_success(self):
        force_refill_user(self.customer, 10)
        self.login_in_bar(self.barmen)
        res = self.submit_basket(
            self.customer, [BasketItem(self.beer.id, 2), BasketItem(self.snack.id, 1)]
        )
        assert res.status_code == 302

        assert self.updated_amount(self.customer) == Decimal("5.5")

        # Test barmen special price

        force_refill_user(self.barmen, 10)

        assert (
            self.submit_basket(self.barmen, [BasketItem(self.beer.id, 1)])
        ).status_code == 302

        assert self.updated_amount(self.barmen) == Decimal("9")

    def test_click_tray_price(self):
        force_refill_user(self.customer, 20)
        self.login_in_bar(self.barmen)

        # Not applying tray price
        res = self.submit_basket(self.customer, [BasketItem(self.beer_tap.id, 2)])
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == Decimal("17")

        # Applying tray price
        res = self.submit_basket(self.customer, [BasketItem(self.beer_tap.id, 7)])
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == Decimal("8")

    def test_click_alcool_unauthorized(self):
        self.login_in_bar()

        for user in [self.underage_customer, self.banned_alcohol_customer]:
            force_refill_user(user, 10)

            # Buy product without age limit
            res = self.submit_basket(user, [BasketItem(self.snack.id, 2)])
            assert res.status_code == 302

            assert self.updated_amount(user) == Decimal("7")

            # Buy product without age limit
            res = self.submit_basket(user, [BasketItem(self.beer.id, 2)])
            assert res.status_code == 200

            assert self.updated_amount(user) == Decimal("7")

    def test_click_unauthorized_customer(self):
        self.login_in_bar()

        for user in [
            self.banned_counter_customer,
            self.customer_old_can_not_buy,
        ]:
            force_refill_user(user, 10)
            resp = self.submit_basket(user, [BasketItem(self.snack.id, 2)])
            assert resp.status_code == 302
            assert resp.url == resolve_url(self.counter)

            assert self.updated_amount(user) == Decimal("10")

    def test_click_user_without_customer(self):
        self.login_in_bar()
        res = self.submit_basket(
            self.customer_can_not_buy, [BasketItem(self.snack.id, 2)]
        )
        assert res.status_code == 404

    def test_click_allowed_old_subscriber(self):
        self.login_in_bar()
        force_refill_user(self.customer_old_can_buy, 10)
        res = self.submit_basket(
            self.customer_old_can_buy, [BasketItem(self.snack.id, 2)]
        )
        assert res.status_code == 302

        assert self.updated_amount(self.customer_old_can_buy) == Decimal("7")

    def test_click_wrong_counter(self):
        self.login_in_bar()
        force_refill_user(self.customer, 10)
        res = self.submit_basket(
            self.customer, [BasketItem(self.snack.id, 2)], counter=self.other_counter
        )
        assertRedirects(res, self.other_counter.get_absolute_url())

        # We want to test sending requests from another counter while
        # we are currently registered to another counter
        # so we connect to a counter and
        # we create a new client, in order to check
        # that using a client not logged to a counter
        # where another client is logged still isn't authorized.
        client = Client()
        res = self.submit_basket(
            self.customer,
            [BasketItem(self.snack.id, 2)],
            counter=self.counter,
            client=client,
        )
        assertRedirects(res, self.counter.get_absolute_url())

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_not_connected(self):
        force_refill_user(self.customer, 10)
        res = self.submit_basket(self.customer, [BasketItem(self.snack.id, 2)])
        assertRedirects(res, self.counter.get_absolute_url())

        res = self.submit_basket(
            self.customer, [BasketItem(self.snack.id, 2)], counter=self.club_counter
        )
        assert res.status_code == 403

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_product_not_in_counter(self):
        force_refill_user(self.customer, 10)
        self.login_in_bar()

        res = self.submit_basket(self.customer, [BasketItem(self.stamps.id, 2)])
        assert res.status_code == 200
        assert self.updated_amount(self.customer) == Decimal("10")

    def test_basket_empty(self):
        force_refill_user(self.customer, 10)

        for basket in [
            [],
            [BasketItem(None, None)],
            [BasketItem(None, None), BasketItem(None, None)],
        ]:
            assertRedirects(
                self.submit_basket(self.customer, basket),
                self.counter.get_absolute_url(),
            )
            assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_product_invalid(self):
        force_refill_user(self.customer, 10)
        self.login_in_bar()

        for item in [
            BasketItem(-1, 2),
            BasketItem(self.beer.id, -1),
            BasketItem(None, 1),
            BasketItem(self.beer.id, None),
        ]:
            assert self.submit_basket(self.customer, [item]).status_code == 200
            assert self.updated_amount(self.customer) == Decimal("10")

    def test_click_not_enough_money(self):
        force_refill_user(self.customer, 10)
        self.login_in_bar()
        res = self.submit_basket(
            self.customer,
            [BasketItem(self.beer_tap.id, 5), BasketItem(self.beer.id, 10)],
        )
        assert res.status_code == 200

        assert self.updated_amount(self.customer) == Decimal("10")

    def test_annotate_has_barman_queryset(self):
        """Test if the custom queryset method `annotate_has_barman` works as intended."""
        counters = Counter.objects.annotate_has_barman(self.barmen)
        for counter in counters:
            if counter in (self.counter, self.other_counter):
                assert counter.has_annotated_barman
            else:
                assert not counter.has_annotated_barman

    def test_selling_ordering(self):
        # Cheaper items should be processed with a higher priority
        self.login_in_bar(self.barmen)
        res = self.submit_basket(
            self.customer, [BasketItem(self.beer.id, 1), BasketItem(self.gift.id, 1)]
        )
        assert res.status_code == 302

        assert self.updated_amount(self.customer) == 0

    def test_recordings(self):
        force_refill_user(self.customer, self.cons.selling_price * 3)
        self.login_in_bar(self.barmen)
        res = self.submit_basket(self.customer, [BasketItem(self.cons.id, 3)])
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == 0
        assert list(
            self.customer.customer.return_balances.values("returnable", "balance")
        ) == [{"returnable": self.cons.cons.id, "balance": 3}]

        res = self.submit_basket(self.customer, [BasketItem(self.dcons.id, 3)])
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == self.dcons.selling_price * -3

        res = self.submit_basket(
            self.customer, [BasketItem(self.dcons.id, self.dcons.dcons.max_return)]
        )
        # from now on, the user amount should not change
        expected_amount = self.dcons.selling_price * (-3 - self.dcons.dcons.max_return)
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == expected_amount

        res = self.submit_basket(self.customer, [BasketItem(self.dcons.id, 1)])
        assert res.status_code == 200
        assert self.updated_amount(self.customer) == expected_amount

        res = self.submit_basket(
            self.customer, [BasketItem(self.cons.id, 1), BasketItem(self.dcons.id, 1)]
        )
        assert res.status_code == 302
        assert self.updated_amount(self.customer) == expected_amount

    def test_recordings_when_negative(self):
        sale_recipe.make(
            customer=self.customer.customer,
            product=self.dcons,
            unit_price=self.dcons.selling_price,
            quantity=10,
        )
        self.customer.customer.update_returnable_balance()
        self.login_in_bar(self.barmen)
        res = self.submit_basket(self.customer, [BasketItem(self.dcons.id, 1)])
        assert res.status_code == 200
        assert self.updated_amount(self.customer) == self.dcons.selling_price * -10

        res = self.submit_basket(self.customer, [BasketItem(self.cons.id, 3)])
        assert res.status_code == 302
        assert (
            self.updated_amount(self.customer)
            == self.dcons.selling_price * -10 - self.cons.selling_price * 3
        )

        res = self.submit_basket(self.customer, [BasketItem(self.beer.id, 1)])
        assert res.status_code == 302
        assert (
            self.updated_amount(self.customer)
            == self.dcons.selling_price * -10
            - self.cons.selling_price * 3
            - self.beer.selling_price
        )

    def test_no_fetch_archived_product(self):
        counter = baker.make(Counter)
        customer = baker.make(Customer)
        product_recipe.make(archived=True, counters=[counter])
        unarchived_products = product_recipe.make(
            archived=False, counters=[counter], _quantity=3
        )
        customer_products = counter.get_products_for(customer)
        assert unarchived_products == customer_products


class TestCounterStats(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = subscriber_user.make(_quantity=4)
        product = product_recipe.make(selling_price=1)
        cls.counter = baker.make(
            Counter, type=["BAR"], sellers=cls.users[:4], products=[product]
        )

        _now = timezone.now()
        permanence_recipe = Recipe(Permanency, counter=cls.counter)
        perms = [
            *[  # total of user 0 : 5 hours
                permanence_recipe.prepare(user=cls.users[0], start=start, end=end)
                for start, end in [
                    (_now, _now + timedelta(hours=1)),
                    (_now + timedelta(hours=4), _now + timedelta(hours=6)),
                    (_now + timedelta(hours=7), _now + timedelta(hours=9)),
                ]
            ],
            *[  # total of user 1 : 16 days, 2 hours, 35 minutes and 54 seconds
                permanence_recipe.prepare(user=cls.users[1], start=start, end=end)
                for start, end in [
                    (_now, _now + timedelta(hours=1)),
                    (
                        _now + timedelta(days=4, hours=1),
                        _now + timedelta(days=20, hours=2, minutes=35, seconds=54),
                    ),
                ]
            ],
            *[  # total of user 2 : 2 hour + 20 hours (but the 20 hours were on last year)
                permanence_recipe.prepare(user=cls.users[2], start=start, end=end)
                for start, end in [
                    (_now + timedelta(days=5), _now + timedelta(days=5, hours=1)),
                    (_now - timedelta(days=300, hours=20), _now - timedelta(days=300)),
                ]
            ],
        ]
        # user 3 has 0 hours of permanence
        Permanency.objects.bulk_create(perms)

        _sale_recipe = Recipe(
            Selling,
            club=cls.counter.club,
            counter=cls.counter,
            product=product,
            unit_price=2,
        )
        sales = [
            *_sale_recipe.prepare(
                quantity=100, customer=cls.users[0].customer, _quantity=10
            ),  # 2000 €
            *_sale_recipe.prepare(
                quantity=100, customer=cls.users[1].customer, _quantity=5
            ),  # 1000 €
            _sale_recipe.prepare(quantity=1, customer=cls.users[2].customer),  # 2€
            _sale_recipe.prepare(quantity=50, customer=cls.users[3].customer),  # 100€
        ]
        Selling.objects.bulk_create(sales)

    def test_not_authenticated_access_fail(self):
        url = reverse("counter:stats", args=[self.counter.id])
        response = self.client.get(url)
        assertRedirects(response, reverse("core:login", query={"next": url}))

    def test_unauthorized_user_fails(self):
        self.client.force_login(baker.make(User))
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 403

    def test_authorized_user_ok(self):
        perm = Permission.objects.get(codename="view_counter_stats")
        self.client.force_login(baker.make(User, user_permissions=[perm]))
        response = self.client.get(reverse("counter:stats", args=[self.counter.id]))
        assert response.status_code == 200

    def test_get_total_sales(self):
        """Test the result of the Counter.get_total_sales() method."""
        assert self.counter.get_total_sales() == 3102

    def test_top_barmen(self):
        """Test the result of Counter.get_top_barmen() is correct."""
        users = [self.users[1], self.users[2], self.users[0]]
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
            for user, perm_time in zip(users, perm_times, strict=True)
        ]

    def test_top_customer(self):
        """Test the result of Counter.get_top_customers() is correct."""
        users = [self.users[0], self.users[1], self.users[3], self.users[2]]
        sale_amounts = [2000, 1000, 100, 2]
        assert list(self.counter.get_top_customers()) == [
            {
                "user": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "promo": user.promo,
                "nickname": user.nick_name,
                "selling_sum": sale_amount,
            }
            for user, sale_amount in zip(users, sale_amounts, strict=True)
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
        """By default, board members should be able to click on office counters"""
        baker.make(Membership, club=self.counter.club, user=self.user, role=3)
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 200

    def test_barman(self):
        """Sellers should be able to click on office counters"""
        self.counter.sellers.add(self.user)
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 200

    def test_both_barman_and_board_member(self):
        """If the user is barman and board member, he should be authorized as well."""
        self.counter.sellers.add(self.user)
        baker.make(Membership, club=self.counter.club, user=self.user, role=3)
        self.client.force_login(self.user)
        res = self.client.get(self.click_url)
        assert res.status_code == 200


@pytest.mark.django_db
class TestCounterLogout:
    def test_logout_simple(self, client: Client):
        perm_counter = baker.make(Counter, type="BAR")
        permanence = baker.make(
            Permanency,
            counter=perm_counter,
            start=now() - timedelta(hours=1),
            activity=now() - timedelta(minutes=10),
        )
        with freeze_time():
            res = client.post(
                reverse("counter:logout", kwargs={"counter_id": permanence.counter_id}),
                data={"user_id": permanence.user_id},
            )
            assertRedirects(
                res,
                reverse(
                    "counter:details", kwargs={"counter_id": permanence.counter_id}
                ),
            )
            permanence.refresh_from_db()
            assert permanence.end == now()

    def test_logout_doesnt_change_old_permanences(self, client: Client):
        perm_counter = baker.make(Counter, type="BAR")
        permanence = baker.make(
            Permanency,
            counter=perm_counter,
            start=now() - timedelta(hours=1),
            activity=now() - timedelta(minutes=10),
        )
        old_end = now() - relativedelta(year=10)
        old_permanence = baker.make(
            Permanency,
            counter=perm_counter,
            end=old_end,
            activity=now() - relativedelta(year=8),
        )
        with freeze_time():
            client.post(
                reverse("counter:logout", kwargs={"counter_id": permanence.counter_id}),
                data={"user_id": permanence.user_id},
            )
            permanence.refresh_from_db()
            assert permanence.end == now()
            old_permanence.refresh_from_db()
            assert old_permanence.end == old_end
