#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#


from django.test import TestCase
from django.urls import reverse

from core.models import User


class TestRefoundAccount(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        # refill skia's account
        cls.skia.customer.amount = 800
        cls.skia.customer.save()
        cls.refound_account_url = reverse("counter:account_refound")

    def test_permission_denied(self):
        self.client.force_login(User.objects.get(username="guy"))
        response_post = self.client.post(
            self.refound_account_url, {"user": self.skia.id}
        )
        response_get = self.client.get(self.refound_account_url)
        assert response_get.status_code == 403
        assert response_post.status_code == 403

    def test_root_granteed(self):
        self.client.force_login(User.objects.get(username="root"))
        response = self.client.post(self.refound_account_url, {"user": self.skia.id})
        self.assertRedirects(response, self.refound_account_url)
        self.skia.refresh_from_db()
        response = self.client.get(self.refound_account_url)
        assert response.status_code == 200
        assert '<form action="" method="post">' in str(response.content)
        assert self.skia.customer.amount == 0

    def test_comptable_granteed(self):
        self.client.force_login(User.objects.get(username="comptable"))
        response = self.client.post(self.refound_account_url, {"user": self.skia.id})
        self.assertRedirects(response, self.refound_account_url)
        self.skia.refresh_from_db()
        response = self.client.get(self.refound_account_url)
        assert response.status_code == 200
        assert '<form action="" method="post">' in str(response.content)
        assert self.skia.customer.amount == 0
