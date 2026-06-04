from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import Club, ClubRole
from core.baker_recipes import subscriber_user
from core.models import Group, User
from election.models import Election, Role


@pytest.mark.django_db
class TestCreateRole(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = baker.make(Club)
        cls.edit_group = baker.make(Group)
        cls.election = baker.make(
            Election,
            clubs=[cls.club],
            edit_groups=[cls.edit_group],
            view_groups=[Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)],
            end_candidature=now() + timedelta(days=1),
        )
        cls.url = reverse(
            "election:create_role", kwargs={"election_id": cls.election.id}
        )
        cls.election_url = reverse(
            "election:detail", kwargs={"election_id": cls.election.id}
        )
        cls.permission = Permission.objects.get(codename="add_role")

    def assert_role_creation_ok(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        response = self.client.post(self.url, data={"title": "foo", "max_choice": 1})
        assertRedirects(response, self.election_url)
        roles = list(self.election.roles.all())
        assert len(roles) == 1
        assert roles[0].title == "foo"

    def assert_role_creation_denied(self):
        initial_role_count = self.election.roles.count()
        response = self.client.get(self.url)
        assert response.status_code == 403
        response = self.client.post(self.url, data={"title": "foo", "max_choice": 1})
        assert response.status_code == 403
        assert self.election.roles.count() == initial_role_count

    def test_admin(self):
        user = baker.make(User, user_permissions=[self.permission])
        self.client.force_login(user)
        self.assert_role_creation_ok()

    def test_edit_group(self):
        user = baker.make(User, groups=[self.edit_group])
        self.client.force_login(user)
        self.assert_role_creation_ok()

    def test_role_linked_to_club_role(self):
        user = baker.make(User, user_permissions=[self.permission])
        self.client.force_login(user)
        club_role = baker.make(ClubRole, is_board=True, club=self.club)
        response = self.client.post(
            self.url, data={"title": "foo", "max_choice": 1, "club_role": club_role.id}
        )
        assertRedirects(response, self.election_url)
        roles = list(self.election.roles.all())
        assert len(roles) == 1
        assert roles[0].title == "foo"
        assert roles[0].club_role == club_role

    def test_permission_denied(self):
        user = subscriber_user.make()
        self.client.force_login(user)
        self.assert_role_creation_denied()

    def test_election_not_editable(self):
        user = baker.make(User, user_permissions=[self.permission])
        self.election.end_candidature = now() - timedelta(minutes=1)
        self.election.save()
        self.client.force_login(user)
        self.assert_role_creation_denied()


class TestUpdateRole(TestCreateRole):
    @classmethod
    def setUpTestData(cls):
        # TestUpdateRole is just TestCreateRole, but with different parameters
        cls.club = baker.make(Club)
        cls.edit_group = baker.make(Group)
        cls.election = baker.make(
            Election,
            clubs=[cls.club],
            edit_groups=[cls.edit_group],
            view_groups=[Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)],
            end_candidature=now() + timedelta(days=1),
        )
        cls.role = baker.make(Role, election=cls.election)
        cls.url = reverse("election:update_role", kwargs={"role_id": cls.role.id})
        cls.election_url = reverse(
            "election:detail", kwargs={"election_id": cls.election.id}
        )
        cls.permission = Permission.objects.get(codename="change_role")
