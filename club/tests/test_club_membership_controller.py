from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate
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
                start_date=localdate() - timedelta(weeks=1),
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[1],
                start_date=localdate() - timedelta(days=1),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[2],
                start_date=localdate() - timedelta(weeks=2),
                end_date=localdate() - timedelta(days=6),
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=localdate() - timedelta(weeks=3),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[2],
                start_date=localdate() - timedelta(days=4),
                end_date=localdate() - timedelta(days=3),
            ),
            # on going
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=localdate() - timedelta(days=1),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[0],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=localdate() - timedelta(weeks=6),
                end_date=localdate() - timedelta(days=3),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[2],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=localdate() - timedelta(weeks=8),
                end_date=localdate() - timedelta(days=6),
            ),
            # former
            Membership.objects.create(
                club=cls.clubs[1],
                user=subscriber_user.make(),
                role=cls.roles[0],
                start_date=localdate() - timedelta(weeks=8),
                end_date=localdate() - timedelta(weeks=7, days=5),
            ),
        ]


class TestNewMembershipAPI(TestMembershipAPI):
    def test_new_membership_one_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = localdate() - timedelta(weeks=1)
        arg = {"since_date": since_date, "clubs_id": self.clubs[0].id}
        url = reverse("api:get_new_clubs_members_since_date")
        with self.assertNumQueries(8):
            response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[0].id]
        assert membership_ids == expected_ids

    def test_new_membership_multiple_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = localdate() - timedelta(weeks=1)
        arg = {
            "since_date": since_date,
            "clubs_id": [self.clubs[0].id, self.clubs[1].id],
        }
        url = reverse("api:get_new_clubs_members_since_date")
        with self.assertNumQueries(11):
            response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[0].id, self.memberships[1].id]
        assert membership_ids == expected_ids

    def test_new_membership_all_clubs(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = localdate() - timedelta(weeks=1)
        arg = {"since_date": since_date}
        url = reverse("api:get_new_clubs_members_since_date")
        with self.assertNumQueries(14):
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
        since_date = localdate() - timedelta(weeks=1)
        arg = {"since_date": since_date, "clubs_id": self.clubs[1].id}
        url = reverse("api:get_former_clubs_members_since_date")
        with self.assertNumQueries(8):
            response = self.client.get(url, arg)

        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[2].id]
        assert membership_ids == expected_ids

    def test_new_membership_multiple_club(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = localdate() - timedelta(weeks=1)
        arg = {
            "since_date": since_date,
            "clubs_id": [self.clubs[1].id, self.clubs[0].id],
        }
        url = reverse("api:get_former_clubs_members_since_date")
        with self.assertNumQueries(11):
            response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [self.memberships[6].id, self.memberships[2].id]
        assert membership_ids == expected_ids

    def test_new_membership_all_clubs(self):
        assert self.user.has_perm("club.view_club")
        self.client.force_login(self.user)
        since_date = localdate() - timedelta(weeks=1)
        arg = {"since_date": since_date}
        url = reverse("api:get_former_clubs_members_since_date")
        with self.assertNumQueries(14):
            response = self.client.get(url, arg)
        assert response.status_code == 200
        data = response.json()

        membership_ids = [e["id"] for e in data]
        expected_ids = [
            self.memberships[7].id,
            self.memberships[6].id,
            self.memberships[2].id,
        ]
        assert membership_ids == expected_ids
