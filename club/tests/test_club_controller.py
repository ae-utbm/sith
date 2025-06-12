import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertNumQueries

from club.models import Club, Membership
from core.baker_recipes import subscriber_user


@pytest.mark.django_db
def test_fetch_club(client: Client):
    club = baker.make(Club)
    baker.make(Membership, club=club, _quantity=10, _bulk_create=True)
    user = subscriber_user.make()
    client.force_login(user)
    with assertNumQueries(7):
        # - 4 queries for authentication
        # - 3 queries for the actual data
        res = client.get(reverse("api:fetch_club", kwargs={"club_id": club.id}))
        assert res.status_code == 200
