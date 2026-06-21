from datetime import date

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from club.models import Club, ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import User


class TestMembershipAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = baker.make(User)
        perm = Permission.objects.get(codename="view_club")
        cls.user.user_permissions.add(perm)
        cls.clubs = baker.make(Club, _quantity=3, is_active=True)
        cls.roles = baker.make(ClubRole, _quantity=3, is_active=True)

        # Clean existing data to avoid side effects
        Membership.objects.all().delete()

        cls.memberships = [
            # on going
            Membership.objects.create(
                club=cls.clubs[0],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=date(2025, 1, 1),
                end_date=None,
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[1],
                start_date=date(2026, 5, 1),
                end_date=None,
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[2],
                start_date=date(2024, 6, 1),
                end_date=date(2025, 8, 1),
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=date(2024, 1, 1),
                end_date=None,
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[2],
                start_date=date(2025, 6, 1),
                end_date=date(2025, 8, 1),
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=date(2026, 6, 6),
                end_date=None,
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[0],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=date(2020, 1, 1),
                end_date=date(2025, 6, 8),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=date(2020, 1, 1),
                end_date=date(2025, 6, 8),
            ),
        ]


class TestNewMembershipAPI(TestMembershipAPI):
    def test_new_membership_one_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {"since_date": since_date, "clubs_id": self.clubs[0].id}
        url = reverse("api:get_new_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[0].id]
        assert membership_ids == expected_ids

    def test_new_membership_multiple_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {
            "since_date": since_date,
            "clubs_id": [self.clubs[0].id, self.clubs[1].id],
        }
        url = reverse("api:get_new_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[0].id, self.memberships[1].id]
        assert membership_ids == expected_ids

    def test_new_membership_all_clubs(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {"since_date": since_date}
        url = reverse("api:get_new_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [
            self.memberships[0].id,
            self.memberships[1].id,
            self.memberships[5].id,
        ]
        assert membership_ids == expected_ids


class TestFormerMembershipAPI(TestMembershipAPI):
    def test_former_membership_one_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {"since_date": since_date, "clubs_id": self.clubs[1].id}
        url = reverse("api:get_former_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[2].id]
        assert membership_ids == expected_ids

    def test_new_membership_multiple_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {
            "since_date": since_date,
            "clubs_id": [self.clubs[1].id, self.clubs[0].id],
        }
        url = reverse("api:get_former_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[6].id, self.memberships[2].id]
        assert membership_ids == expected_ids

    def test_new_membership_all_clubs(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = date(2025, 1, 1)
        arg = {"since_date": since_date}
        url = reverse("api:get_former_clubs_members_since_date")
        response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [
            self.memberships[6].id,
            self.memberships[7].id,
            self.memberships[2].id,
        ]
        assert membership_ids == expected_ids
