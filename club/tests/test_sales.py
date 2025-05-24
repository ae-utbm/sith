import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from club.forms import SellingsForm
from club.models import Club
from core.models import User
from counter.baker_recipes import product_recipe, sale_recipe
from counter.models import Counter, Customer


@pytest.mark.django_db
def test_sales_page_doesnt_crash(client: Client):
    club = baker.make(Club)
    admin = baker.make(User, is_superuser=True)
    client.force_login(admin)
    response = client.get(reverse("club:club_sellings", kwargs={"club_id": club.id}))
    assert response.status_code == 200


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
