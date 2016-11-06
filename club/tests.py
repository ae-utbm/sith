from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User
from club.models import Club

# Create your tests here.

class ClubTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.rbatsbak = User.objects.filter(username="rbatsbak").first()
        self.guy = User.objects.filter(username="guy").first()
        self.bdf = Club.objects.filter(unix_name="bdf").first()

    def test_create_add_user_to_club_from_root_ok(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.skia.id, "role": 3})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":self.bdf.id}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("S&#39; Kia</a></td>\\n                <td>Responsable info</td>" in str(response.content))

    def test_create_add_user_to_club_from_root_fail_not_subscriber(self):
        self.client.login(username='root', password='plop')
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.guy.id, "role": 3})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<ul class="errorlist nonfield"><li>' in str(response.content))
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":self.bdf.id}))
        self.assertFalse("Guy Carlier</a></td>\\n                <td>Responsable info</td>" in str(response.content))

    def test_create_add_user_to_club_from_root_fail_already_in_club(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.skia.id, "role": 3})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":self.bdf.id}))
        self.assertTrue("S&#39; Kia</a></td>\\n                <td>Responsable info</td>" in str(response.content))
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.skia.id, "role": 4})
        self.assertTrue(response.status_code == 200)
        self.assertFalse("S&#39; Kia</a></td>\\n                <td>Secrétaire</td>" in str(response.content))

    def test_create_add_user_to_club_from_skia_ok(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.skia.id, "role": 10})
        self.client.login(username='skia', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.rbatsbak.id, "role": 9})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":self.bdf.id}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("""Richard Batsbak</a></td>\\n                <td>Vice-Pr\\xc3\\xa9sident</td>""" in str(response.content))

    def test_create_add_user_to_club_from_richard_fail(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.rbatsbak.id, "role": 3})
        self.client.login(username='rbatsbak', password='plop')
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":self.bdf.id}), {"user": self.skia.id, "role": 10})
        self.assertTrue(response.status_code == 200)
        self.assertTrue("<li>You do not have the permission to do that</li>" in str(response.content))

