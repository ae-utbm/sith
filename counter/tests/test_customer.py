import itertools
import string
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.base_user import make_password
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker

from club.models import Membership
from core.baker_recipes import board_user, subscriber_user
from core.models import User
from counter.baker_recipes import product_recipe, refill_recipe, sale_recipe
from counter.models import (
    Counter,
    Customer,
    Refilling,
    ReturnableProduct,
    Selling,
    StudentCard,
)


class TestStudentCard(TestCase):
    """Tests for adding and deleting Stundent Cards
    Test that an user can be found with it's student card.
    """

    @classmethod
    def setUpTestData(cls):
        cls.customer = subscriber_user.make()
        cls.barmen = subscriber_user.make(password=make_password("plop"))
        cls.board_admin = board_user.make()
        cls.club_admin = baker.make(User)
        cls.root = baker.make(User, is_superuser=True)
        cls.subscriber = subscriber_user.make()

        cls.counter = baker.make(Counter, type="BAR")
        cls.counter.sellers.add(cls.barmen)

        cls.club_counter = baker.make(Counter)
        baker.make(
            Membership,
            start_date=now() - timedelta(days=30),
            club=cls.club_counter.club,
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
            user=cls.club_admin,
        )

        cls.valid_card = baker.make(
            StudentCard, customer=cls.customer.customer, uid="8A89B82018B0A0"
        )

    def login_in_counter(self):
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": self.barmen.username, "password": "plop"},
        )

    def invalid_uids(self) -> list[tuple[str, str]]:
        """Return a list of invalid uids, with the associated error message"""
        return [
            ("8B90734A802A8", ""),  # too short
            (
                "8B90734A802A8FA",
                "Assurez-vous que cette valeur comporte au plus 14 caractères (actuellement 15).",
            ),  # too long
            ("8b90734a802a9f", ""),  # has lowercases
            (" " * 14, "Ce champ est obligatoire."),  # empty
            (
                self.customer.customer.student_card.uid,
                "Un objet Carte étudiante avec ce champ Uid existe déjà.",
            ),
        ]

    def test_search_user_with_student_card(self):
        self.login_in_counter()
        response = self.client.post(
            reverse("counter:details", args=[self.counter.id]),
            {"code": self.valid_card.uid},
        )

        assert response.url == reverse(
            "counter:click",
            kwargs={"counter_id": self.counter.id, "user_id": self.customer.pk},
        )

    def test_add_student_card_from_counter(self):
        self.login_in_counter()
        for uid in ["8B90734A802A8F", "ABCAAAFAAFAAAB", "15248196326518"]:
            customer = subscriber_user.make().customer
            response = self.client.post(
                reverse(
                    "counter:add_student_card", kwargs={"customer_id": customer.pk}
                ),
                {"uid": uid},
                HTTP_REFERER=reverse(
                    "counter:click",
                    kwargs={"counter_id": self.counter.id, "user_id": customer.pk},
                ),
            )
            assert response.status_code == 302
            customer.refresh_from_db()
            assert hasattr(customer, "student_card")
            assert customer.student_card.uid == uid

    def test_add_student_card_from_counter_fail(self):
        self.login_in_counter()
        customer = subscriber_user.make().customer
        for uid, error_msg in self.invalid_uids():
            response = self.client.post(
                reverse(
                    "counter:add_student_card", kwargs={"customer_id": customer.pk}
                ),
                {"uid": uid},
                HTTP_REFERER=reverse(
                    "counter:click",
                    kwargs={"counter_id": self.counter.id, "user_id": customer.pk},
                ),
            )
            self.assertContains(response, text="Cet UID est invalide")
            self.assertContains(response, text=error_msg)
            customer.refresh_from_db()
            assert not hasattr(customer, "student_card")

    def test_add_student_card_from_counter_unauthorized(self):
        def send_valid_request(client, counter_id):
            return client.post(
                reverse(
                    "counter:add_student_card", kwargs={"customer_id": self.customer.pk}
                ),
                {"uid": "8B90734A802A8F"},
                HTTP_REFERER=reverse(
                    "counter:click",
                    kwargs={"counter_id": counter_id, "user_id": self.customer.pk},
                ),
            )

        # Send to a counter where you aren't logged in
        assert send_valid_request(self.client, self.counter.id).status_code == 403

        self.login_in_counter()
        barman = subscriber_user.make()
        self.counter.sellers.add(barman)
        # We want to test sending requests from another counter while
        # we are currently registered to another counter
        # so we connect to a counter and
        # we create a new client, in order to check
        # that using a client not logged to a counter
        # where another client is logged still isn't authorized.
        client = Client()
        # Send to a counter where you aren't logged in
        assert send_valid_request(client, self.counter.id).status_code == 403

        # Send to a non bar counter
        client.force_login(self.club_admin)
        assert send_valid_request(client, self.club_counter.id).status_code == 403

    def test_delete_student_card_with_owner(self):
        self.client.force_login(self.customer)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            )
        )
        self.customer.customer.refresh_from_db()
        assert not hasattr(self.customer.customer, "student_card")

    def test_delete_student_card_with_admin_user(self):
        """Test that AE board members and root users can delete student cards"""
        for user in self.board_admin, self.root:
            self.client.force_login(user)
            self.client.post(
                reverse(
                    "counter:delete_student_card",
                    kwargs={"customer_id": self.customer.customer.pk},
                )
            )
            self.customer.customer.refresh_from_db()
            assert not hasattr(self.customer.customer, "student_card")

    def test_delete_student_card_from_counter(self):
        self.login_in_counter()
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            http_referer=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.customer.customer.refresh_from_db()
        assert not hasattr(self.customer.customer, "student_card")

    def test_delete_student_card_fail(self):
        """Test that non-admin users cannot delete student cards"""
        self.client.force_login(self.subscriber)
        response = self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            )
        )
        assert response.status_code == 403
        self.subscriber.customer.refresh_from_db()
        assert not hasattr(self.subscriber.customer, "student_card")

    def test_add_student_card_from_user_preferences(self):
        users = [self.customer, self.board_admin, self.root]
        uids = ["8B90734A802A8F", "ABCAAAFAAFAAAB", "15248196326518"]
        for user, uid in itertools.product(users, uids):
            self.customer.customer.student_card.delete()
            self.client.force_login(user)
            response = self.client.post(
                reverse(
                    "counter:add_student_card",
                    kwargs={"customer_id": self.customer.customer.pk},
                ),
                {"uid": uid},
            )
            assert response.status_code == 302
            response = self.client.get(response.url)

            self.customer.customer.refresh_from_db()
            assert self.customer.customer.student_card.uid == uid
            self.assertContains(response, text="Carte enregistrée")

    def test_add_student_card_from_user_preferences_fail(self):
        customer = subscriber_user.make()
        self.client.force_login(customer)
        for uid, error_msg in self.invalid_uids():
            url = reverse(
                "counter:add_student_card", kwargs={"customer_id": customer.customer.pk}
            )
            response = self.client.post(url, {"uid": uid})
            self.assertContains(response, text="Cet UID est invalide")
            self.assertContains(response, text=error_msg)
            customer.refresh_from_db()
            assert not hasattr(customer.customer, "student_card")


class TestCustomerAccountId(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create(
            username="a", password="plop", email="a.a@a.fr"
        )
        user_b = User.objects.create(username="b", password="plop", email="b.b@b.fr")
        user_c = User.objects.create(username="c", password="plop", email="c.c@c.fr")
        Customer.objects.create(user=cls.user_a, amount=10, account_id="1111a")
        Customer.objects.create(user=user_b, amount=0, account_id="9999z")
        Customer.objects.create(user=user_c, amount=0, account_id="12345f")

    def test_create_customer(self):
        user_d = User.objects.create(username="d", password="plop")
        customer, created = Customer.get_or_create(user_d)
        account_id = customer.account_id
        number = account_id[:-1]
        assert created is True
        assert number == "12346"
        assert len(account_id) == 6
        assert account_id[-1] in string.ascii_lowercase
        assert customer.amount == 0

    def test_get_existing_account(self):
        account, created = Customer.get_or_create(self.user_a)
        assert created is False
        assert account.account_id == "1111a"
        assert account.amount == 10


@pytest.mark.django_db
def test_update_balance():
    customers = baker.make(Customer, _quantity=5, _bulk_create=True)
    refills = [
        *refill_recipe.prepare(
            customer=iter(customers),
            amount=iter([30, 30, 40, 50, 50]),
            _quantity=len(customers),
            _save_related=True,
        ),
        refill_recipe.prepare(customer=customers[0], amount=30, _save_related=True),
        refill_recipe.prepare(customer=customers[4], amount=10, _save_related=True),
    ]
    Refilling.objects.bulk_create(refills)
    sales = [
        *sale_recipe.prepare(
            customer=iter(customers),
            _quantity=len(customers),
            unit_price=10,
            quantity=1,
            _save_related=True,
        ),
        *sale_recipe.prepare(
            customer=iter(customers[:3]),
            _quantity=3,
            unit_price=5,
            quantity=2,
            _save_related=True,
        ),
        sale_recipe.prepare(
            customer=customers[4],
            quantity=1,
            unit_price=50,
            _save_related=True,
        ),
        *sale_recipe.prepare(
            # all customers also bought products without using their AE account.
            # All purchases made with another mean than the AE account should
            # be ignored when updating the account balance.
            customer=iter(customers),
            _quantity=len(customers),
            unit_price=50,
            quantity=1,
            payment_method=Selling.PaymentMethod.CARD,
            _save_related=True,
        ),
    ]
    Selling.objects.bulk_create(sales)
    # customer 0 = 40, customer 1 = 10€, customer 2 = 20€,
    # customer 3 = 40€, customer 4 = 0€
    customers_qs = Customer.objects.filter(pk__in={c.pk for c in customers})
    # put everything at zero to be sure the amounts were wrong beforehand
    customers_qs.update(amount=0)
    customers_qs.update_amount()
    for customer, amount in zip(customers, [40, 10, 20, 40, 0], strict=False):
        customer.refresh_from_db()
        assert customer.amount == amount


@pytest.mark.django_db
def test_update_returnable_balance():
    ReturnableProduct.objects.all().delete()
    customer = baker.make(Customer)
    products = product_recipe.make(selling_price=0, _quantity=4, _bulk_create=True)
    returnables = [
        baker.make(
            ReturnableProduct, product=products[0], returned_product=products[1]
        ),
        baker.make(
            ReturnableProduct, product=products[2], returned_product=products[3]
        ),
    ]
    balance_qs = ReturnableProduct.objects.annotate_balance_for(customer)
    assert not customer.return_balances.exists()
    assert list(balance_qs.values_list("balance", flat=True)) == [0, 0]

    sale_recipe.make(customer=customer, product=products[0], unit_price=0, quantity=5)
    sale_recipe.make(customer=customer, product=products[2], unit_price=0, quantity=1)
    sale_recipe.make(customer=customer, product=products[3], unit_price=0, quantity=3)
    customer.update_returnable_balance()
    assert list(customer.return_balances.values("returnable_id", "balance")) == [
        {"returnable_id": returnables[0].id, "balance": 5},
        {"returnable_id": returnables[1].id, "balance": -2},
    ]
    assert set(balance_qs.values_list("balance", flat=True)) == {-2, 5}
