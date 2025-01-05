from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.models import Group, User
from election.models import Election


class TestElection(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.election = Election.objects.first()
        cls.public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
        cls.sli = User.objects.get(username="sli")
        cls.subscriber = User.objects.get(username="subscriber")
        cls.public = User.objects.get(username="public")


class TestElectionDetail(TestElection):
    def test_permission_denied(self):
        self.election.view_groups.remove(self.public_group)
        self.client.force_login(self.public)
        response = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        assert response.status_code == 403

    def test_permisson_granted(self):
        self.client.force_login(self.public)
        response = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        assert response.status_code == 200
        assert "La roue tourne" in str(response.content)


class TestElectionUpdateView(TestElection):
    def test_permission_denied(self):
        self.client.force_login(self.subscriber)
        response = self.client.get(
            reverse("election:update", args=str(self.election.id))
        )
        assert response.status_code == 403
        response = self.client.post(
            reverse("election:update", args=str(self.election.id))
        )
        assert response.status_code == 403
