import json
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
from counter.baker_recipes import refill_recipe, sale_recipe
from counter.models import (
    BillingInfo,
    Counter,
    Customer,
    Refilling,
    Selling,
    StudentCard,
)


@pytest.mark.django_db
class TestBillingInfo:
    @pytest.fixture
    def payload(self):
        return {
            "first_name": "Subscribed",
            "last_name": "User",
            "address_1": "3, rue de Troyes",
            "zip_code": "34301",
            "city": "Sète",
            "country": "FR",
            "phone_number": "0612345678",
        }

    def test_edit_infos(self, client: Client, payload: dict):
        user = subscriber_user.make()
        baker.make(BillingInfo, customer=user.customer)
        client.force_login(user)
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        user.refresh_from_db()
        infos = BillingInfo.objects.get(customer__user=user)
        assert response.status_code == 200
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        for key, val in payload.items():
            assert getattr(infos, key) == val

    @pytest.mark.parametrize(
        "user_maker", [subscriber_user.make, lambda: baker.make(User)]
    )
    @pytest.mark.django_db
    def test_create_infos(self, client: Client, user_maker, payload):
        user = user_maker()
        client.force_login(user)
        assert not BillingInfo.objects.filter(customer__user=user).exists()
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert hasattr(user, "customer")
        infos = BillingInfo.objects.get(customer__user=user)
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        for key, val in payload.items():
            assert getattr(infos, key) == val

    def test_invalid_data(self, client: Client, payload: dict[str, str]):
        user = subscriber_user.make()
        client.force_login(user)
        # address_1, zip_code and country are missing
        del payload["city"]
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 422
        user.customer.refresh_from_db()
        assert not hasattr(user.customer, "billing_infos")

    @pytest.mark.parametrize(
        ("operator_maker", "expected_code"),
        [
            (subscriber_user.make, 403),
            (lambda: baker.make(User), 403),
            (lambda: baker.make(User, is_superuser=True), 200),
        ],
    )
    def test_edit_other_user(
        self, client: Client, operator_maker, expected_code: int, payload: dict
    ):
        user = subscriber_user.make()
        client.force_login(operator_maker())
        baker.make(BillingInfo, customer=user.customer)
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == expected_code

    @pytest.mark.parametrize(
        "phone_number",
        ["+33612345678", "0612345678", "06 12 34 56 78", "06-12-34-56-78"],
    )
    def test_phone_number_format(
        self, client: Client, payload: dict, phone_number: str
    ):
        """Test that various formats of phone numbers are accepted."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = phone_number
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        infos = BillingInfo.objects.get(customer__user=user)
        assert infos.phone_number == "0612345678"
        assert infos.phone_number.country_code == 33

    def test_foreign_phone_number(self, client: Client, payload: dict):
        """Test that a foreign phone number is accepted."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = "+49612345678"
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        infos = BillingInfo.objects.get(customer__user=user)
        assert infos.phone_number.as_national == "06123 45678"
        assert infos.phone_number.country_code == 49

    @pytest.mark.parametrize(
        "phone_number", ["061234567a", "06 12 34 56", "061234567879", "azertyuiop"]
    )
    def test_invalid_phone_number(
        self, client: Client, payload: dict, phone_number: str
    ):
        """Test that invalid phone numbers are rejected."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = phone_number
        response = client.put(
            reverse("api:put_billing_info", args=[user.id]),
            json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 422
        assert not BillingInfo.objects.filter(customer__user=user).exists()


class TestStudentCard(TestCase):
    """Tests for adding and deleting Stundent Cards
    Test that an user can be found with it's student card.
    """

    @classmethod
    def setUpTestData(cls):
        cls.customer = subscriber_user.make()
        cls.customer.save()
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

    def setUp(self):
        # Auto login on counter
        self.client.post(
            reverse("counter:login", args=[self.counter.id]),
            {"username": self.barmen.username, "password": "plop"},
        )

    def test_search_user_with_student_card(self):
        response = self.client.post(
            reverse("counter:details", args=[self.counter.id]),
            {"code": self.valid_card.uid},
        )

        assert response.url == reverse(
            "counter:click",
            kwargs={"counter_id": self.counter.id, "user_id": self.customer.id},
        )

    def test_add_student_card_from_counter(self):
        # Test card with mixed letters and numbers
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "8B90734A802A8F"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        assert response.status_code == 302
        self.assertContains(self.client.get(response.url), text="8B90734A802A8F")

        # Test card with only numbers
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "04786547890123"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        assert response.status_code == 302
        self.assertContains(self.client.get(response.url), text="04786547890123")

        # Test card with only letters
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "ABCAAAFAAFAAAB"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        assert response.status_code == 302
        self.assertContains(self.client.get(response.url), text="ABCAAAFAAFAAAB")

    def test_add_student_card_from_counter_fail(self):
        # UID too short
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "8B90734A802A8"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.assertContains(response, text="Cet UID est invalide")

        # UID too long
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "8B90734A802A8FA"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.assertContains(response, text="Cet UID est invalide")
        self.assertContains(
            response,
            text="Assurez-vous que cette valeur comporte au plus 14 caractères (actuellement 15).",
        )

        # Test with already existing card
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": self.valid_card.uid},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.assertContains(response, text="Cet UID est invalide")
        self.assertContains(
            response, text="Un objet Student card avec ce champ Uid existe déjà."
        )

        # Test with lowercase
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "8b90734a802a9f"},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with white spaces
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                },
            ),
            {"uid": "              "},
            HTTP_REFERER=reverse(
                "counter:click",
                kwargs={
                    "counter_id": self.counter.id,
                    "user_id": self.customer.customer.pk,
                },
            ),
        )
        self.assertContains(response, text="Cet UID est invalide")
        self.assertContains(response, text="Ce champ est obligatoire.")

    def test_add_student_card_from_counter_unauthorized(self):
        # Send to a counter where you aren't logged in
        self.client.post(
            reverse("counter:logout", args=[self.counter.id]),
            {"user_id": self.barmen.id},
        )

        def send_valid_request(client, counter_id):
            return client.post(
                reverse(
                    "counter:add_student_card",
                    kwargs={
                        "customer_id": self.customer.customer.pk,
                    },
                ),
                {"uid": "8B90734A802A8F"},
                HTTP_REFERER=reverse(
                    "counter:click",
                    kwargs={
                        "counter_id": counter_id,
                        "user_id": self.customer.customer.pk,
                    },
                ),
            )

        assert send_valid_request(self.client, self.counter.id).status_code == 403

        # Send to a non bar counter
        self.client.force_login(self.club_admin)
        assert send_valid_request(self.client, self.club_counter.id).status_code == 403

    def test_delete_student_card_with_owner(self):
        self.client.force_login(self.customer)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                    "card_id": self.customer.customer.student_cards.first().id,
                },
            )
        )
        assert not self.customer.customer.student_cards.exists()

    def test_delete_student_card_with_board_member(self):
        self.client.force_login(self.board_admin)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                    "card_id": self.customer.customer.student_cards.first().id,
                },
            )
        )
        assert not self.customer.customer.student_cards.exists()

    def test_delete_student_card_with_root(self):
        self.client.force_login(self.root)
        self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                    "card_id": self.customer.customer.student_cards.first().id,
                },
            )
        )
        assert not self.customer.customer.student_cards.exists()

    def test_delete_student_card_fail(self):
        self.client.force_login(self.subscriber)
        response = self.client.post(
            reverse(
                "counter:delete_student_card",
                kwargs={
                    "customer_id": self.customer.customer.pk,
                    "card_id": self.customer.customer.student_cards.first().id,
                },
            )
        )
        assert response.status_code == 403
        assert self.customer.customer.student_cards.exists()

    def test_add_student_card_from_user_preferences(self):
        # Test with owner of the card
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8F"},
        )

        assert response.status_code == 302

        response = self.client.get(response.url)
        self.assertContains(response, text="8B90734A802A8F")

        # Test with board member
        self.client.force_login(self.board_admin)
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8A"},
        )

        assert response.status_code == 302

        response = self.client.get(response.url)
        self.assertContains(response, text="8B90734A802A8A")

        # Test card with only numbers
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "04786547890123"},
        )
        assert response.status_code == 302

        response = self.client.get(response.url)
        self.assertContains(response, text="04786547890123")

        # Test card with only letters
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "ABCAAAFAAFAAAB"},
        )

        assert response.status_code == 302

        response = self.client.get(response.url)
        self.assertContains(response, text="ABCAAAFAAFAAAB")

        # Test with root
        self.client.force_login(self.root)
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8B"},
        )

        assert response.status_code == 302

        response = self.client.get(response.url)
        self.assertContains(response, text="8B90734A802A8B")

    def test_add_student_card_from_user_preferences_fail(self):
        self.client.force_login(self.customer)
        # UID too short
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8"},
        )

        self.assertContains(response, text="Cet UID est invalide")

        # UID too long
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8FA"},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with already existing card
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": self.valid_card.uid},
        )
        self.assertContains(
            response, text="Un objet Student card avec ce champ Uid existe déjà."
        )

        # Test with lowercase
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8b90734a802a9f"},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with white spaces
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": " " * 14},
        )
        self.assertContains(response, text="Cet UID est invalide")

        # Test with unauthorized user
        self.client.force_login(self.subscriber)
        response = self.client.post(
            reverse(
                "counter:add_student_card",
                kwargs={"customer_id": self.customer.customer.pk},
            ),
            {"uid": "8B90734A802A8F"},
        )
        assert response.status_code == 403


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
            customer=customers[4], quantity=1, unit_price=50, _save_related=True
        ),
    ]
    Selling.objects.bulk_create(sales)
    # customer 0 = 40, customer 1 = 10€, customer 2 = 20€,
    # customer 3 = 40€, customer 4 = 0€
    customers_qs = Customer.objects.filter(pk__in={c.pk for c in customers})
    # put everything at zero to be sure the amounts were wrong beforehand
    customers_qs.update(amount=0)
    customers_qs.update_amount()
    for customer, amount in zip(customers, [40, 10, 20, 40, 0]):
        customer.refresh_from_db()
        assert customer.amount == amount
