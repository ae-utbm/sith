from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from model_bakery.recipe import Recipe

from club.models import Club, Membership
from club.schemas import UserMembershipSchema
from core.baker_recipes import subscriber_user
from core.models import Page


class TestFetchClub(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = subscriber_user.make()
        pages = baker.make(Page, _quantity=3, _bulk_create=True)
        clubs = baker.make(Club, page=iter(pages), _quantity=3, _bulk_create=True)
        recipe = Recipe(
            Membership, user=cls.user, start_date=localdate() - timedelta(days=2)
        )
        cls.members = Membership.objects.bulk_create(
            [
                recipe.prepare(club=clubs[0]),
                recipe.prepare(club=clubs[1], end_date=localdate() - timedelta(days=1)),
                recipe.prepare(club=clubs[1]),
            ]
        )

    def test_fetch_memberships(self):
        self.client.force_login(subscriber_user.make())
        res = self.client.get(
            reverse("api:fetch_user_clubs", kwargs={"user_id": self.user.id})
        )
        assert res.status_code == 200
        assert [UserMembershipSchema.model_validate(m) for m in res.json()] == [
            UserMembershipSchema.from_orm(m) for m in (self.members[0], self.members[2])
        ]

    def test_fetch_club_nb_queries(self):
        self.client.force_login(subscriber_user.make())
        with self.assertNumQueries(6):
            # - 5 queries for authentication
            # - 1 query for the actual data
            res = self.client.get(
                reverse("api:fetch_user_clubs", kwargs={"user_id": self.user.id})
            )
            assert res.status_code == 200
