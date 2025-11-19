import csv
import itertools

import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from club.forms import SellingsForm
from club.models import Club
from core.models import User
from counter.baker_recipes import product_recipe, sale_recipe
from counter.models import Counter, Customer, Product, Selling


@pytest.mark.django_db
def test_sales_page_doesnt_crash(client: Client):
    """Basic crashtest on club sales view."""
    club = baker.make(Club)
    product = baker.make(Product, club=club)
    admin = baker.make(User, is_superuser=True)
    client.force_login(admin)
    url = reverse("club:club_sellings", kwargs={"club_id": club.id})
    assert client.get(url).status_code == 200
    assert client.post(url).status_code == 200
    assert client.post(url, data={"products": [product.id]}).status_code == 200


@pytest.mark.django_db
def test_sales_form_counter_filter():
    """Test that counters are properly filtered in SellingsForm"""
    club = baker.make(Club)
    counters = baker.make(
        Counter, _quantity=5, _bulk_create=True, name=iter(["Z", "a", "B", "e", "f"])
    )
    counters[0].club = club
    counters[0].save()
    sale_recipe.make(
        counter=counters[1], club=club, unit_price=0, customer=baker.make(Customer)
    )
    product_recipe.make(counters=[counters[2]], club=club)

    form = SellingsForm(club)
    form_counters = list(form.fields["counters"].queryset)
    assert form_counters == [counters[1], counters[2], counters[0]]


@pytest.mark.django_db
def test_club_sales_csv(client: Client):
    client.force_login(baker.make(User, is_superuser=True))
    club = baker.make(Club)
    counter = baker.make(Counter, club=club)
    product = product_recipe.make(club=club, counters=[counter], purchase_price=0.5)
    customers = baker.make(Customer, amount=100, _quantity=2, _bulk_create=True)
    sales: list[Selling] = sale_recipe.make(
        club=club,
        counter=counter,
        quantity=2,
        unit_price=1.5,
        product=iter([product, product, None]),
        customer=itertools.cycle(customers),
        _quantity=3,
    )
    url = reverse("club:sellings_csv", kwargs={"club_id": club.id})
    response = client.post(url, data={"counters": [counter.id]})
    assert response.status_code == 200
    reader = csv.reader(s.decode() for s in response.streaming_content)
    data = list(reader)
    sale_rows = [
        [
            str(s.date),
            str(counter),
            str(s.seller),
            s.customer.user.get_display_name(),
            s.label,
            "2",
            "1.50",
            "3.00",
            "Compte utilisateur",
        ]
        for s in sales[::-1]
    ]
    sale_rows[2].extend(["0.50", "1.00"])
    sale_rows[1].extend(["0.50", "1.00"])
    sale_rows[0].extend(["", ""])
    assert data == [
        ["Quantité", "6"],
        ["Total", "9"],
        ["Bénéfice", "1"],
        [
            "Date",
            "Comptoir",
            "Barman",
            "Client",
            "Étiquette",
            "Quantité",
            "Prix unitaire",
            "Total",
            "Méthode de paiement",
            "Prix d'achat",
            "Bénéfice",
        ],
        *sale_rows,
    ]
