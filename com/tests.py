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
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import html
from django.utils.timezone import localtime, now
from django.utils.translation import gettext as _

from club.models import Club, Membership
from com.models import News, Poster, Sith, Weekmail, WeekmailArticle
from core.models import AnonymousUser, RealGroup, User


@pytest.fixture()
def user_community():
    return User.objects.get(username="comunity")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        reverse("com:alert_edit"),
        reverse("com:info_edit"),
    ],
)
def test_com_page_is_working(client, url, user_community):
    client.force_login(user_community)
    response = client.get(url)
    assert response.status_code == 200


class ComTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        cls.com_group = RealGroup.objects.filter(
            id=settings.SITH_GROUP_COM_ADMIN_ID
        ).first()
        cls.skia.groups.set([cls.com_group])

    def setUp(self):
        self.client.force_login(self.skia)

    def test_alert_msg(self):
        self.client.post(
            reverse("com:alert_edit"),
            {
                "alert_msg": """
### ALERTE!

**Caaaataaaapuuuulte!!!!**
"""
            },
        )
        r = self.client.get(reverse("core:index"))
        self.assertContains(
            r,
            """<div id="alert_box">
                            <div class="markdown"><h3>ALERTE!</h3>
<p><strong>Caaaataaaapuuuulte!!!!</strong></p>""",
        )

    def test_info_msg(self):
        self.client.post(
            reverse("com:info_edit"),
            {
                "info_msg": """
### INFO: **Caaaataaaapuuuulte!!!!**
"""
            },
        )
        r = self.client.get(reverse("core:index"))
        self.assertContains(
            r,
            """<div id="info_box">
                            <div class="markdown"><h3>INFO: <strong>Caaaataaaapuuuulte!!!!</strong></h3>""",
        )

    def test_birthday_non_subscribed_user(self):
        self.client.force_login(User.objects.get(username="guy"))
        response = self.client.get(reverse("core:index"))
        self.assertContains(
            response,
            text=html.escape(
                _("You need an up to date subscription to access this content")
            ),
        )

    def test_birthday_subscibed_user(self):
        response = self.client.get(reverse("core:index"))

        self.assertNotContains(
            response,
            text=html.escape(
                _("You need an up to date subscription to access this content")
            ),
        )


class SithTest(TestCase):
    def test_sith_owner(self):
        """
        Test that the sith instance is owned by com admins
        and nobody else
        """
        sith: Sith = Sith.objects.first()

        com_admin = User.objects.get(username="comunity")
        assert sith.is_owned_by(com_admin)

        anonymous = AnonymousUser()
        assert not sith.is_owned_by(anonymous)

        sli = User.objects.get(username="sli")
        assert not sith.is_owned_by(sli)


class NewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.com_admin = User.objects.get(username="comunity")
        new = News.objects.create(
            title="dummy new",
            summary="This is a dummy new",
            content="Look at that beautiful dummy new",
            author=User.objects.get(username="subscriber"),
            club=Club.objects.first(),
        )
        cls.new = new
        cls.author = new.author
        cls.sli = User.objects.get(username="sli")
        cls.anonymous = AnonymousUser()

    def test_news_owner(self):
        """
        Test that news are owned by com admins
        or by their author but nobody else
        """

        assert self.new.is_owned_by(self.com_admin)
        assert self.new.is_owned_by(self.author)
        assert not self.new.is_owned_by(self.anonymous)
        assert not self.new.is_owned_by(self.sli)

    def test_news_viewer(self):
        """
        Test that moderated news can be viewed by anyone
        and not moderated news only by com admins
        """
        # by default a news isn't moderated
        assert self.new.can_be_viewed_by(self.com_admin)
        assert not self.new.can_be_viewed_by(self.sli)
        assert not self.new.can_be_viewed_by(self.anonymous)
        assert not self.new.can_be_viewed_by(self.author)

        self.new.is_moderated = True
        self.new.save()
        assert self.new.can_be_viewed_by(self.com_admin)
        assert self.new.can_be_viewed_by(self.sli)
        assert self.new.can_be_viewed_by(self.anonymous)
        assert self.new.can_be_viewed_by(self.author)

    def test_news_editor(self):
        """
        Test that only com admins can edit news
        """
        assert self.new.can_be_edited_by(self.com_admin)
        assert not self.new.can_be_edited_by(self.sli)
        assert not self.new.can_be_edited_by(self.anonymous)
        assert not self.new.can_be_edited_by(self.author)


class WeekmailArticleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.com_admin = User.objects.get(username="comunity")
        author = User.objects.get(username="subscriber")
        cls.article = WeekmailArticle.objects.create(
            weekmail=Weekmail.objects.create(),
            author=author,
            title="title",
            content="Some content",
            club=Club.objects.first(),
        )
        cls.author = author
        cls.sli = User.objects.get(username="sli")
        cls.anonymous = AnonymousUser()

    def test_weekmail_owner(self):
        """
        Test that weekmails are owned only by com admins
        """
        assert self.article.is_owned_by(self.com_admin)
        assert not self.article.is_owned_by(self.author)
        assert not self.article.is_owned_by(self.anonymous)
        assert not self.article.is_owned_by(self.sli)


class PosterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.com_admin = User.objects.get(username="comunity")
        cls.poster = Poster.objects.create(
            name="dummy",
            file=SimpleUploadedFile("dummy.jpg", b"azertyuiop"),
            club=Club.objects.first(),
            date_begin=localtime(now()),
        )
        cls.sli = User.objects.get(username="sli")
        cls.sli.memberships.all().delete()
        Membership(user=cls.sli, club=Club.objects.first(), role=5).save()
        cls.susbcriber = User.objects.get(username="subscriber")
        cls.anonymous = AnonymousUser()

    def test_poster_owner(self):
        """
        Test that poster are owned by com admins and board members in clubs
        """
        assert self.poster.is_owned_by(self.com_admin)
        assert not self.poster.is_owned_by(self.anonymous)

        assert not self.poster.is_owned_by(self.susbcriber)
        assert self.poster.is_owned_by(self.sli)
