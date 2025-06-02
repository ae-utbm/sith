from datetime import date

import pytest
from model_bakery import baker

from club.models import Club
from counter.models import InvoiceCall


@pytest.mark.django_db
def test_invoice_date_with_date():
    club = baker.make(Club)
    invoice = InvoiceCall.objects.create(club=club, month=date(2025, 10, 20))

    assert not invoice.is_validated
    assert str(invoice) == f"invoice call of {invoice.month} made by {club}"
    assert invoice.month == date(2025, 10, 1)


@pytest.mark.django_db
def test_invoice_date_with_string():
    club = baker.make(Club)
    invoice = InvoiceCall.objects.create(club=club, month="2025-10")

    assert invoice.month == date(2025, 10, 1)


@pytest.mark.django_db
def test_invoice_call_invalid_month_string():
    club = baker.make(Club)

    with pytest.raises(ValueError):
        InvoiceCall.objects.create(club=club, month="2025-13")
