from typing import Callable

import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import subscriber_user
from core.models import User
from counter.models import BillingInfo


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

    def test_not_authorized(self, client: Client, payload: dict[str, str]):
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assertRedirects(
            response,
            reverse("core:login", query={"next": reverse("eboutic:billing_infos")}),
        )

    def test_edit_infos(self, client: Client, payload: dict[str, str]):
        user = subscriber_user.make()
        baker.make(BillingInfo, customer=user.customer)
        client.force_login(user)
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        user.refresh_from_db()
        infos = BillingInfo.objects.get(customer__user=user)
        assert response.status_code == 302
        assert hasattr(user.customer, "billing_infos")
        assert infos.customer == user.customer
        for key, val in payload.items():
            assert getattr(infos, key) == val

    @pytest.mark.parametrize(
        "user_maker", [subscriber_user.make, lambda: baker.make(User)]
    )
    def test_create_infos(
        self, client: Client, user_maker: Callable[[], User], payload: dict[str, str]
    ):
        user = user_maker()
        client.force_login(user)
        assert not BillingInfo.objects.filter(customer__user=user).exists()
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assert response.status_code == 302
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
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assert response.status_code == 200
        user.customer.refresh_from_db()
        assert not hasattr(user.customer, "billing_infos")

    @pytest.mark.parametrize(
        "phone_number",
        ["+33612345678", "0612345678", "06 12 34 56 78", "06-12-34-56-78"],
    )
    def test_phone_number_format(
        self, client: Client, payload: dict[str, str], phone_number: str
    ):
        """Test that various formats of phone numbers are accepted."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = phone_number
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assert response.status_code == 302
        infos = BillingInfo.objects.get(customer__user=user)
        assert infos.phone_number == "0612345678"
        assert infos.phone_number.country_code == 33

    def test_foreign_phone_number(self, client: Client, payload: dict[str, str]):
        """Test that a foreign phone number is accepted."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = "+49612345678"
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assert response.status_code == 302
        infos = BillingInfo.objects.get(customer__user=user)
        assert infos.phone_number.as_national == "06123 45678"
        assert infos.phone_number.country_code == 49

    @pytest.mark.parametrize(
        "phone_number", ["061234567a", "06 12 34 56", "061234567879", "azertyuiop"]
    )
    def test_invalid_phone_number(
        self, client: Client, payload: dict[str, str], phone_number: str
    ):
        """Test that invalid phone numbers are rejected."""
        user = subscriber_user.make()
        client.force_login(user)
        payload["phone_number"] = phone_number
        response = client.post(
            reverse("eboutic:billing_infos"),
            payload,
        )
        assert response.status_code == 200
        assert not BillingInfo.objects.filter(customer__user=user).exists()
