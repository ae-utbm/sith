from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.conf import settings
from datetime import date, datetime

from core.models import User, Group
from election.models import Election, Role, ElectionList, Candidature, Vote


class MainElection():
    election = Election.objects.all().first()
    public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
    subscriber_group = Group.objects.get(name=settings.SITH_MAIN_MEMBERS_GROUP)
    ae_board_group = Group.objects.get(name=settings.SITH_MAIN_BOARD_GROUP)
    sli = User.objects.get(username='sli')
    subscriber = User.objects.get(username='subscriber')
    public = User.objects.get(username='public')


class ElectionDetailTest(MainElection, TestCase):
    def setUp(self):
        call_command("populate")

    def test_permission_denied(self):
        self.election.view_groups.remove(self.public_group)
        self.election.view_groups.add(self.subscriber_group)
        self.election.save()
        self.client.login(username=self.public.username, password='plop')
        response_get = self.client.get(reverse('election:detail',
                                       args=str(self.election.id)))
        response_post = self.client.get(reverse('election:detail',
                                        args=str(self.election.id)))
        self.assertTrue(response_get.status_code == 403)
        self.assertTrue(response_post.status_code == 403)
        self.election.view_groups.remove(self.subscriber_group)
        self.election.view_groups.add(self.public_group)
        self.election.save()

    def test_permisson_granted(self):
        self.client.login(username=self.public.username, password='plop')
        response_get = self.client.get(reverse('election:detail',
                                       args=str(self.election.id)))
        response_post = self.client.post(reverse('election:detail',
                                         args=str(self.election.id)))
        self.assertFalse(response_get.status_code == 403)
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue('La roue tourne' in str(response_get.content))
