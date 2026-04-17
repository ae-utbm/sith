from collections.abc import Callable

import pytest
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from model_bakery import baker, seq
from model_bakery.recipe import Recipe
from pytest_django.asserts import assertRedirects

from club.forms import ClubRoleFormSet
from club.models import Club, ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import AnonymousUser, User


def make_club():
    # unittest-style tests cannot use fixture, so we create a function
    # that will be callable either by a pytest fixture or inside
    # a TestCase.setUpTestData method.
    club = baker.make(Club)
    recipe = Recipe(ClubRole, club=club, name=seq("role "))
    recipe.make(
        is_board=iter([True, True, False]),
        is_presidency=iter([True, False, False]),
        order=iter([1, 2, 3]),
        _quantity=3,
        _bulk_create=True,
    )
    return club


@pytest.fixture
def club(db):
    """A club with a presidency role, a board role and a member role"""
    return make_club()


@pytest.mark.django_db
def test_order_auto(club):
    """Test that newly created roles are put in the right place."""
    roles = list(club.roles.all())
    # create new roles one by one (like they will be in prod)
    # each new role should be placed at the end of its category
    recipe = Recipe(ClubRole, club=club, name=seq("new role "))
    role_a = recipe.make(is_board=True, is_presidency=True, order=None)
    role_b = recipe.make(is_board=True, is_presidency=False, order=None)
    role_c = recipe.make(is_board=False, is_presidency=False, order=None)
    assert list(club.roles.order_by("order")) == [
        roles[0],
        role_a,
        roles[1],
        role_b,
        roles[2],
        role_c,
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_factory", "is_allowed"),
    [
        (
            lambda club: baker.make(
                User,
                user_permissions=[Permission.objects.get(codename="change_clubrole")],
            ),
            True,
        ),
        (  # user with presidency roles can edit the club roles
            lambda club: subscriber_user.make(
                memberships=[
                    baker.make(
                        Membership,
                        club=club,
                        role=club.roles.filter(is_presidency=True).first(),
                    )
                ]
            ),
            True,
        ),
        (  # user in the board but not in the presidency cannot edit roles
            lambda club: subscriber_user.make(
                memberships=[
                    baker.make(
                        Membership,
                        club=club,
                        role=club.roles.filter(
                            is_presidency=False, is_board=True
                        ).first(),
                    )
                ]
            ),
            False,
        ),
        (lambda _: AnonymousUser(), False),
    ],
)
def test_can_roles_be_edited_by(
    club: Club, user_factory: Callable[[Club], User], is_allowed
):
    """Test that `Club.can_roles_be_edited_by` return the right value"""
    user = user_factory(club)
    assert club.can_roles_be_edited_by(user) == is_allowed


@pytest.mark.django_db
@pytest.mark.parametrize(
    ["route", "is_presidency", "is_board"],
    [
        ("club:new_role_president", True, True),
        ("club:new_role_board", False, True),
        ("club:new_role_member", False, False),
    ],
)
def test_create_role_view(client: Client, route: str, is_presidency, is_board):
    """Test that the role creation views work."""
    club = baker.make(Club)
    role = baker.make(ClubRole, club=club, is_presidency=True, is_board=True)
    user = subscriber_user.make()
    baker.make(Membership, club=club, role=role, user=user, end_date=None)
    url = reverse(route, kwargs={"club_id": club.id})
    client.force_login(user)

    res = client.get(url)
    assert res.status_code == 200

    res = client.post(url, data={"name": "foo"})
    assertRedirects(res, reverse("club:club_roles", kwargs={"club_id": club.id}))
    new_role = club.roles.last()
    assert new_role.name == "foo"
    assert new_role.is_presidency == is_presidency
    assert new_role.is_board == is_board


class TestClubRoleUpdate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = make_club()
        cls.roles = list(cls.club.roles.all())
        cls.user = subscriber_user.make()
        baker.make(
            Membership, club=cls.club, role=cls.roles[0], user=cls.user, end_date=None
        )
        cls.url = reverse("club:club_roles", kwargs={"club_id": cls.club.id})

    def setUp(self):
        self.payload = {
            "roles-TOTAL_FORMS": 3,
            "roles-INITIAL_FORMS": 3,
            "roles-MIN_NUM_FORMS": 0,
            "roles-MAX_NUM_FORMS": 1000,
            "roles-0-ORDER": self.roles[0].order,
            "roles-0-id": self.roles[0].id,
            "roles-0-club": self.club.id,
            "roles-0-is_presidency": True,
            "roles-0-is_board": True,
            "roles-0-name": self.roles[0].name,
            "roles-0-description": self.roles[0].description,
            "roles-0-is_active": True,
            "roles-1-ORDER": self.roles[1].order,
            "roles-1-id": self.roles[1].id,
            "roles-1-club": self.club.id,
            "roles-1-is_presidency": False,
            "roles-1-is_board": True,
            "roles-1-name": self.roles[1].name,
            "roles-1-description": self.roles[1].description,
            "roles-1-is_active": True,
            "roles-2-ORDER": self.roles[2].order,
            "roles-2-id": self.roles[2].id,
            "roles-2-club": self.club.id,
            "roles-2-is_presidency": False,
            "roles-2-is_board": False,
            "roles-2-name": self.roles[2].name,
            "roles-2-description": self.roles[2].description,
            "roles-2-is_active": True,
        }

    def test_view_ok(self):
        """Basic test to check that the view works."""
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        assert res.status_code == 200
        self.payload["roles-2-name"] = "foo"
        res = self.client.post(self.url, data=self.payload)
        assertRedirects(res, self.url)
        self.roles[2].refresh_from_db()
        assert self.roles[2].name == "foo"

    def test_incoherent_order(self):
        """Test that placing a member role over a board role fails."""
        self.payload["roles-0-ORDER"] = 4
        formset = ClubRoleFormSet(data=self.payload, instance=self.club)
        assert not formset.is_valid()
        assert formset.errors == [
            {
                "__all__": [
                    f"Le rôle {self.roles[0].name} ne peut pas "
                    "être placé en-dessous d'un rôle de membre.",
                    f"Le rôle {self.roles[0].name} ne peut pas être placé "
                    "en-dessous d'un rôle qui n'est pas de la présidence.",
                ]
            },
            {},
            {},
        ]

    def test_change_order_ok(self):
        """Test that changing order the intended way works"""
        self.payload["roles-1-ORDER"] = 3
        self.payload["roles-1-is_board"] = False
        self.payload["roles-2-ORDER"] = 2
        formset = ClubRoleFormSet(data=self.payload, instance=self.club)
        assert formset.is_valid()
        formset.save()
        assert list(self.club.roles.order_by("order")) == [
            self.roles[0],
            self.roles[2],
            self.roles[1],
        ]
        self.roles[1].refresh_from_db()
        assert not self.roles[1].is_board

    def test_non_board_presidency_is_forbidden(self):
        """Test that a role cannot be in the presidency without being in the board."""
        self.payload["roles-0-is_board"] = False
        formset = ClubRoleFormSet(data=self.payload, instance=self.club)
        assert not formset.is_valid()
        assert formset.errors == [
            {
                "__all__": [
                    "Un rôle ne peut pas appartenir à la présidence sans être dans le bureau",
                ]
            },
            {},
            {},
        ]

    def test_president_moves_itself_out_of_the_presidency(self):
        """Test that if the user moves its own role out of the presidency,
        then it's redirected to another page and loses access to the update page."""
        self.payload["roles-0-is_presidency"] = False
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=self.payload)
        assertRedirects(
            res, reverse("club:club_members", kwargs={"club_id": self.club.id})
        )
        # When the user clicked that button, it still had the right to update roles,
        # so the modification should be applied
        self.roles[0].refresh_from_db()
        assert self.roles[0].is_presidency is False

        res = self.client.get(self.url)
        assert res.status_code == 403
