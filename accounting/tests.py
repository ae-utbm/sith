from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.conf import settings

from core.models import User
from counter.models import Counter


class RefoundAccountTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        # reffil skia's account
        self.skia.customer.amount = 800
        self.skia.customer.save()

    def test_permission_denied(self):
        self.client.login(useername='guy', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertTrue(response_get.status_code == 403)
        self.assertTrue(response_post.status_code == 403)

    def test_root_granteed(self):
        self.client.login(username='root', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        self.skia = User.objects.filter(username='skia').first()
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertFalse(response_get.status_code == 403)
        self.assertTrue('<form action="" method="post">' in str(response_get.content))
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue(self.skia.customer.amount == 0)

    def test_comptable_granteed(self):
        self.client.login(username='comptable', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        self.skia = User.objects.filter(username='skia').first()
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertFalse(response_get.status_code == 403)
        self.assertTrue('<form action="" method="post">' in str(response_get.content))
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue(self.skia.customer.amount == 0)
