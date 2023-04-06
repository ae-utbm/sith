# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from django.test import TestCase
from django.urls import reverse

from core.models import Group, User
from election.models import Election


class ElectionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.election = Election.objects.first()
        cls.public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
        cls.subscriber_group = Group.objects.get(name=settings.SITH_MAIN_MEMBERS_GROUP)
        cls.ae_board_group = Group.objects.get(name=settings.SITH_MAIN_BOARD_GROUP)
        cls.sli = User.objects.get(username="sli")
        cls.subscriber = User.objects.get(username="subscriber")
        cls.public = User.objects.get(username="public")


class ElectionDetailTest(ElectionTest):
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


class ElectionUpdateView(ElectionTest):
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
