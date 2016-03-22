from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

# Create your tests here.

class ClubTest(TestCase):
    def setUp(self):
        call_command("populate")

    def test_create_add_user_to_club_from_root_ok(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 2, "role": 3})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":4}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("<li>Woenzel&#39;UT - skia - Responsable info</li>" in str(response.content))

    def test_create_add_user_to_club_from_root_fail_not_subscriber(self):
        self.client.login(username='root', password='plop')
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 3, "role": 3})
        self.assertTrue(response.status_code == 200)
        self.assertTrue("User must be subscriber to take part to a club" in str(response.content))
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":4}))
        self.assertFalse("<li>Woenzel&#39;UT - guy - Responsable info</li>" in str(response.content))

    def test_create_add_user_to_club_from_root_fail_already_in_club(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 2, "role": 3})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":4}))
        self.assertTrue("<li>Woenzel&#39;UT - skia - Responsable info</li>" in str(response.content))
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 2, "role": 4})
        self.assertTrue(response.status_code == 200)
        self.assertFalse("<li>Woenzel&#39;UT - skia - Secrétaire</li>" in str(response.content))

    def test_create_add_user_to_club_from_skia_ok(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 2, "role": 10})
        self.client.login(username='skia', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 4, "role": 9})
        response = self.client.get(reverse("club:club_members", kwargs={"club_id":4}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("<li>Woenzel&#39;UT - rbatsbak - Vice-Pr" in str(response.content))

    def test_create_add_user_to_club_from_skia_fail(self):
        self.client.login(username='root', password='plop')
        self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 2, "role": 3})
        self.client.login(username='skia', password='plop')
        response = self.client.post(reverse("club:club_members", kwargs={"club_id":4}), {"user": 4, "role": 10})
        self.assertTrue(response.status_code == 200)
        self.assertTrue("<li>You do not have the permission to do that</li>" in str(response.content))
