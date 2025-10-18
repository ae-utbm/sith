from datetime import date, datetime

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import Club
from core.models import User
from counter.baker_recipes import sale_recipe
from counter.forms import InvoiceCallForm
from counter.models import Customer, InvoiceCall, Selling


@pytest.mark.django_db
@pytest.mark.parametrize(
    "month", [date(2025, 10, 20), "2025-10", datetime(2025, 10, 15, 12, 30)]
)
def test_invoice_date_with_date(month: date | datetime | str):
    club = baker.make(Club)
    invoice = InvoiceCall.objects.create(club=club, month=month)
    invoice.refresh_from_db()
    assert not invoice.is_validated
    assert invoice.month == date(2025, 10, 1)


@pytest.mark.django_db
def test_invoice_call_invalid_month_string():
    club = baker.make(Club)

    with pytest.raises(ValidationError):
        InvoiceCall.objects.create(club=club, month="2025-13")


@pytest.mark.django_db
@pytest.mark.parametrize("query", [None, {"month": "2025-08"}])
def test_invoice_call_view(client: Client, query: dict | None):
    user = baker.make(
        User,
        user_permissions=[
            *Permission.objects.filter(
                codename__in=["view_invoicecall", "change_invoicecall"]
            )
        ],
    )
    client.force_login(user)
    url = reverse("counter:invoices_call", query=query)
    assert client.get(url).status_code == 200
    assertRedirects(client.post(url), url)


@pytest.mark.django_db
def test_invoice_call_form():
    Selling.objects.all().delete()
    month = localdate() - relativedelta(months=1)
    clubs = baker.make(Club, _quantity=2)
    recipe = sale_recipe.extend(date=month, customer=baker.make(Customer, amount=10000))
    recipe.make(club=clubs[0], quantity=2, unit_price=200)
    recipe.make(club=clubs[0], quantity=3, unit_price=5)
    recipe.make(club=clubs[1], quantity=20, unit_price=10)
    form = InvoiceCallForm(
        month=month, data={str(clubs[0].id): True, str(clubs[1].id): False}
    )
    assert form.is_valid()
    form.save()
    assert InvoiceCall.objects.filter(
        club=clubs[0], month=month, is_validated=True
    ).exists()
    assert InvoiceCall.objects.filter(
        club=clubs[1], month=month, is_validated=False
    ).exists()
