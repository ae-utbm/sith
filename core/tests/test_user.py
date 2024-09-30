from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker, seq
from model_bakery.recipe import Recipe

from core.baker_recipes import subscriber_user
from core.models import User


class TestSearchUsers(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.all().delete()
        user_recipe = Recipe(
            User,
            first_name=seq("First", suffix="Name"),
            last_name=seq("Last", suffix="Name"),
            nick_name=seq("Nick", suffix="Name"),
        )
        cls.users = [
            user_recipe.make(last_login=None),
            *user_recipe.make(
                last_login=seq(now() - timedelta(days=30), timedelta(days=1)),
                _quantity=10,
                _bulk_create=True,
            ),
        ]
        call_command("update_index", "core", "--remove")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # restore the index
        call_command("update_index", "core", "--remove")


class TestSearchUsersAPI(TestSearchUsers):
    def test_order(self):
        """Test that users are ordered by last login date."""
        self.client.force_login(subscriber_user.make())

        response = self.client.get(reverse("api:search_users") + "?search=First")
        assert response.status_code == 200
        assert response.json()["count"] == 11
        # The users are ordered by last login date, so we need to reverse the list
        assert [r["id"] for r in response.json()["results"]] == [
            u.id for u in self.users[::-1]
        ]

    def test_search_case_insensitive(self):
        """Test that the search is case insensitive."""
        self.client.force_login(subscriber_user.make())

        expected = [u.id for u in self.users[::-1]]
        for term in ["first", "First", "FIRST"]:
            response = self.client.get(reverse("api:search_users") + f"?search={term}")
            assert response.status_code == 200
            assert response.json()["count"] == 11
            assert [r["id"] for r in response.json()["results"]] == expected

    def test_search_nick_name(self):
        """Test that the search can be done on the nick name."""
        self.client.force_login(subscriber_user.make())

        # this should return users with nicknames Nick11, Nick10 and Nick1
        response = self.client.get(reverse("api:search_users") + "?search=Nick1")
        assert response.status_code == 200
        assert [r["id"] for r in response.json()["results"]] == [
            self.users[10].id,
            self.users[9].id,
            self.users[0].id,
        ]

    def test_search_special_characters(self):
        """Test that the search can be done on special characters."""
        belix = baker.make(User, nick_name="Bélix")
        call_command("update_index", "core")
        self.client.force_login(subscriber_user.make())

        # this should return users with first names First1 and First10
        response = self.client.get(reverse("api:search_users") + "?search=bél")
        assert response.status_code == 200
        assert [r["id"] for r in response.json()["results"]] == [belix.id]


class TestSearchUsersView(TestSearchUsers):
    """Test the search user view (`GET /search`)."""

    def test_page_ok(self):
        """Just test that the page loads."""
        self.client.force_login(subscriber_user.make())
        response = self.client.get(reverse("core:search"))
        assert response.status_code == 200
