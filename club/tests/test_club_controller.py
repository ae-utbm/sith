from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertNumQueries

from club.models import Club, Membership
from core.baker_recipes import subscriber_user


@pytest.mark.django_db
class TestFetchClub:
    @pytest.fixture()
    def club(self):
        club = baker.make(Club)
        last_month = date.today() - timedelta(days=30)
        yesterday = date.today() - timedelta(days=1)
        membership_recipe = Recipe(Membership, club=club, start_date=last_month)
        membership_recipe.make(end_date=None, _quantity=10, _bulk_create=True)
        membership_recipe.make(end_date=yesterday, _quantity=10, _bulk_create=True)
        return club

    def test_fetch_club_members(self, client: Client, club: Club):
        user = subscriber_user.make()
        client.force_login(user)
        res = client.get(reverse("api:fetch_club", kwargs={"club_id": club.id}))
        assert res.status_code == 200
        member_ids = {member["user"]["id"] for member in res.json()["members"]}
        assert member_ids == set(
            club.members.ongoing().values_list("user_id", flat=True)
        )

    def test_fetch_club_nb_queries(self, client: Client, club: Club):
        user = subscriber_user.make()
        client.force_login(user)
        with assertNumQueries(6):
            # - 4 queries for authentication
            # - 2 queries for the actual data
            res = client.get(reverse("api:fetch_club", kwargs={"club_id": club.id}))
            assert res.status_code == 200
