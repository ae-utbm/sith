from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.conf import settings

from core.models import User, Group
from election.models import Election


class MainElection(TestCase):
    def setUp(self):
        call_command("populate")

        self.election = Election.objects.all().first()
        self.public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
        self.subscriber_group = Group.objects.get(name=settings.SITH_MAIN_MEMBERS_GROUP)
        self.ae_board_group = Group.objects.get(name=settings.SITH_MAIN_BOARD_GROUP)
        self.sli = User.objects.get(username="sli")
        self.subscriber = User.objects.get(username="subscriber")
        self.public = User.objects.get(username="public")


class ElectionDetailTest(MainElection):
    def test_permission_denied(self):
        self.election.view_groups.remove(self.public_group)
        self.election.view_groups.add(self.subscriber_group)
        self.election.save()
        self.client.login(username=self.public.username, password="plop")
        response_get = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        response_post = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        self.assertTrue(response_get.status_code == 403)
        self.assertTrue(response_post.status_code == 403)
        self.election.view_groups.remove(self.subscriber_group)
        self.election.view_groups.add(self.public_group)
        self.election.save()

    def test_permisson_granted(self):
        self.client.login(username=self.public.username, password="plop")
        response_get = self.client.get(
            reverse("election:detail", args=str(self.election.id))
        )
        response_post = self.client.post(
            reverse("election:detail", args=str(self.election.id))
        )
        self.assertFalse(response_get.status_code == 403)
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue("La roue tourne" in str(response_get.content))


class ElectionUpdateView(MainElection):
    def test_permission_denied(self):
        self.client.login(username=self.subscriber.username, password="plop")
        response_get = self.client.get(
            reverse("election:update", args=str(self.election.id))
        )
        response_post = self.client.post(
            reverse("election:update", args=str(self.election.id))
        )
        self.assertTrue(response_get.status_code == 403)
        self.assertTrue(response_post.status_code == 403)
