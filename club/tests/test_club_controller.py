import pytest
from model_bakery import baker
from ninja_extra.testing import TestClient
from pytest_django.asserts import assertNumQueries

from club.api import ClubController
from club.models import Club, Membership


@pytest.mark.django_db
def test_fetch_club():
    club = baker.make(Club)
    baker.make(Membership, club=club, _quantity=10, _bulk_create=True)
    with assertNumQueries(3):
        res = TestClient(ClubController).get(f"/{club.id}")
        assert res.status_code == 200
