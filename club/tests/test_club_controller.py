from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertNumQueries

from club.models import Club, Membership
from core.baker_recipes import subscriber_user
from core.models import Group, Page, User


class TestClubSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:search_club")
        cls.user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="access_lookup")]
        )
        # delete existing clubs to avoid side effect
        groups = list(
            Group.objects.exclude(club=None, club_board=None).values_list(
                "id", flat=True
            )
        )
        Page.objects.exclude(club=None).delete()
        Club.objects.all().delete()
        Group.objects.filter(id__in=groups).delete()

        cls.clubs = baker.make(
            Club,
            _quantity=5,
            name=iter(["AE", "ae 1", "Troll", "Dev AE", "pdf"]),
            is_active=True,
        )

    def test_inactive_club(self):
        self.client.force_login(self.user)
        inactive_ids = {self.clubs[0].id, self.clubs[2].id}
        Club.objects.filter(id__in=inactive_ids).update(is_active=False)
        response = self.client.get(self.url, {"is_active": False})
        assert response.status_code == 200
        assert {d["id"] for d in response.json()["results"]} == inactive_ids

    def test_excluded_id(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"exclude_ids": [self.clubs[1].id]})
        assert response.status_code == 200
        ids = {d["id"] for d in response.json()["results"]}
        assert ids == {c.id for c in [self.clubs[0], *self.clubs[2:]]}

    def test_club_search(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"search": "AE"})
        assert response.status_code == 200
        ids = {d["id"] for d in response.json()["results"]}
        assert ids == {c.id for c in [self.clubs[0], self.clubs[1], self.clubs[3]]}


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
