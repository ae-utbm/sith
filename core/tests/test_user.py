from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib import auth
from django.core.management import call_command
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import DetailView
from model_bakery import baker, seq
from model_bakery.recipe import Recipe, foreign_key
from pytest_django.asserts import assertRedirects

from com.models import News
from core.baker_recipes import (
    old_subscriber_user,
    subscriber_user,
    very_old_subscriber_user,
)
from core.models import Group, User
from core.views import UserTabsMixin
from counter.models import Counter, Refilling, Selling
from eboutic.models import Invoice, InvoiceItem


class TestSearchUsers(TestCase):
    @classmethod
    def setUpTestData(cls):
        # News.author has on_delete=PROTECT, so news must be deleted beforehand
        News.objects.all().delete()
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
            response = self.client.get(
                reverse("api:search_users", query={"search": term})
            )
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


@pytest.mark.django_db
def test_user_account_not_found(client: Client):
    client.force_login(baker.make(User, is_superuser=True))
    user = baker.make(User)
    res = client.get(reverse("core:user_account", kwargs={"user_id": user.id}))
    assert res.status_code == 404
    res = client.get(
        reverse(
            "core:user_account_detail",
            kwargs={"user_id": user.id, "year": 2024, "month": 10},
        )
    )
    assert res.status_code == 404


class TestFilterInactive(TestCase):
    @classmethod
    def setUpTestData(cls):
        time_active = now() - settings.SITH_ACCOUNT_INACTIVITY_DELTA + timedelta(days=1)
        time_inactive = time_active - timedelta(days=3)
        counter, seller = baker.make(Counter), baker.make(User)
        sale_recipe = Recipe(
            Selling,
            counter=counter,
            club=counter.club,
            seller=seller,
            is_validated=True,
        )

        cls.users = [
            baker.make(User),
            subscriber_user.make(),
            old_subscriber_user.make(),
            *very_old_subscriber_user.make(_quantity=3),
        ]
        sale_recipe.make(customer=cls.users[3].customer, date=time_active)
        baker.make(
            Refilling, customer=cls.users[4].customer, date=time_active, counter=counter
        )
        sale_recipe.make(customer=cls.users[5].customer, date=time_inactive)

    def test_filter_inactive(self):
        res = User.objects.filter(id__in=[u.id for u in self.users]).filter_inactive()
        assert list(res) == [self.users[0], self.users[5]]


@pytest.mark.django_db
def test_user_invoice_with_multiple_items():
    """Test that annotate_total() works when invoices contain multiple items."""
    user: User = subscriber_user.make()
    item_recipe = Recipe(InvoiceItem, invoice=foreign_key(Recipe(Invoice, user=user)))
    item_recipe.make(_quantity=3, quantity=1, product_unit_price=5)
    item_recipe.make(_quantity=1, quantity=1, product_unit_price=5)
    item_recipe.make(_quantity=2, quantity=1, product_unit_price=iter([5, 8]))
    res = list(
        Invoice.objects.filter(user=user)
        .annotate_total()
        .order_by("-total")
        .values_list("total", flat=True)
    )
    assert res == [15, 13, 5]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("first_name", "last_name", "expected"),
    [
        ("Auguste", "Bartholdi", "abartholdi2"),  # ville du lion rpz
        ("Aristide", "Denfert-Rochereau", "adenfertrochereau"),
        ("John", "Dôe", "jdoe"),  # with an accent
    ],
)
def test_generate_username(first_name: str, last_name: str, expected: str):
    baker.make(
        User,
        username=iter(["abar", "abartholdi", "abartholdi1", "abar1"]),
        _quantity=4,
        _bulk_create=True,
    )
    new_user = User(first_name=first_name, last_name=last_name, email="a@example.com")
    new_user.generate_username()
    assert new_user.username == expected


@pytest.mark.django_db
def test_user_added_to_public_group():
    """Test that newly created users are added to the public group"""
    user = baker.make(User)
    assert user.groups.filter(pk=settings.SITH_GROUP_PUBLIC_ID).exists()
    assert user.is_in_group(pk=settings.SITH_GROUP_PUBLIC_ID)


@pytest.mark.django_db
def test_user_update_groups(client: Client):
    client.force_login(baker.make(User, is_superuser=True))
    manageable_groups = baker.make(Group, is_manually_manageable=True, _quantity=3)
    hidden_groups = baker.make(Group, is_manually_manageable=False, _quantity=4)
    user = baker.make(User, groups=[*manageable_groups[1:], *hidden_groups[:3]])
    response = client.post(
        reverse("core:user_groups", kwargs={"user_id": user.id}),
        data={"groups": [manageable_groups[0].id, manageable_groups[1].id]},
    )
    assertRedirects(response, user.get_absolute_url())
    # only the manually manageable groups should have changed
    assert set(user.groups.all()) == {
        Group.objects.get(pk=settings.SITH_GROUP_PUBLIC_ID),
        manageable_groups[0],
        manageable_groups[1],
        *hidden_groups[:3],
    }


@pytest.mark.django_db
def test_logout(client: Client):
    user = baker.make(User)
    client.force_login(user)
    res = client.post(reverse("core:logout"))
    assertRedirects(res, reverse("core:login"))
    assert auth.get_user(client).is_anonymous


class UserTabTestView(UserTabsMixin, DetailView): ...


@pytest.mark.django_db
@pytest.mark.parametrize(
    ["user_factory", "expected_tabs"],
    [
        (
            subscriber_user.make,
            [
                "infos",
                "godfathers",
                "pictures",
                "tools",
                "edit",
                "prefs",
                "clubs",
                "stats",
                "account",
            ],
        ),
        (
            # this user is superuser, but still won't see a few tabs,
            # because he is not subscribed
            lambda: baker.make(User, is_superuser=True),
            [
                "infos",
                "godfathers",
                "pictures",
                "tools",
                "edit",
                "prefs",
                "clubs",
                "groups",
            ],
        ),
    ],
)
def test_displayed_user_self_tabs(user_factory, expected_tabs: list[str]):
    """Test that a user can view the appropriate tabs in its own profile"""
    user = user_factory()
    request = RequestFactory().get("")
    request.user = user
    view = UserTabTestView()
    view.setup(request)
    view.object = user
    tabs = [tab["slug"] for tab in view.get_list_of_tabs()]
    assert tabs == expected_tabs


@pytest.mark.django_db
@pytest.mark.parametrize(
    ["user_factory", "expected_tabs"],
    [
        (subscriber_user.make, ["infos", "godfathers", "pictures", "clubs"]),
        (
            # this user is superuser, but still won't see a few tabs,
            # because he is not subscribed
            lambda: baker.make(User, is_superuser=True),
            [
                "infos",
                "godfathers",
                "pictures",
                "edit",
                "prefs",
                "clubs",
                "groups",
                "stats",
                "account",
            ],
        ),
    ],
)
def test_displayed_other_user_tabs(user_factory, expected_tabs: list[str]):
    """Test that a user can view the appropriate tabs in another user's profile."""
    request_user = user_factory()
    request = RequestFactory().get("")
    request.user = request_user
    view = UserTabTestView()
    view.setup(request)
    view.object = subscriber_user.make()  # user whose page is being seen
    tabs = [tab["slug"] for tab in view.get_list_of_tabs()]
    assert tabs == expected_tabs
