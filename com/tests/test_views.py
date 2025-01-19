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
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import html
from django.utils.timezone import localtime, now
from django.utils.translation import gettext as _
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from club.models import Club, Membership
from com.models import News, NewsDate, Poster, Sith, Weekmail, WeekmailArticle
from core.baker_recipes import subscriber_user
from core.models import AnonymousUser, Group, User


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


class TestCom(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        cls.com_group = Group.objects.get(id=settings.SITH_GROUP_COM_ADMIN_ID)
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
        assert r.status_code == 200
        self.assertInHTML(
            """<div id="alert_box"><div class="markdown"><h3>ALERTE!</h3>
            <p><strong>Caaaataaaapuuuulte!!!!</strong></p>""",
            r.content.decode(),
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

        assert r.status_code == 200
        self.assertInHTML(
            """<div id="info_box"><div class="markdown">
            <h3>INFO: <strong>Caaaataaaapuuuulte!!!!</strong></h3>""",
            r.content.decode(),
        )

    def test_birthday_non_subscribed_user(self):
        self.client.force_login(User.objects.get(username="guy"))
        response = self.client.get(reverse("core:index"))
        self.assertContains(
            response,
            text=html.escape(_("You need to subscribe to access this content")),
        )

    def test_birthday_subscibed_user(self):
        response = self.client.get(reverse("core:index"))

        self.assertNotContains(
            response,
            text=html.escape(_("You need to subscribe to access this content")),
        )

    def test_birthday_old_subscibed_user(self):
        self.client.force_login(User.objects.get(username="old_subscriber"))
        response = self.client.get(reverse("core:index"))

        self.assertNotContains(
            response,
            text=html.escape(_("You need to subscribe to access this content")),
        )


class TestSith(TestCase):
    def test_sith_owner(self):
        """Test that the sith instance is owned by com admins and nobody else."""
        sith: Sith = Sith.objects.first()

        com_admin = User.objects.get(username="comunity")
        assert sith.is_owned_by(com_admin)

        anonymous = AnonymousUser()
        assert not sith.is_owned_by(anonymous)

        sli = User.objects.get(username="sli")
        assert not sith.is_owned_by(sli)


class TestNews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.com_admin = User.objects.get(username="comunity")
        cls.new = baker.make(News)
        cls.author = cls.new.author
        cls.sli = User.objects.get(username="sli")
        cls.anonymous = AnonymousUser()

    def test_news_owner(self):
        """Test that news are owned by com admins
        or by their author but nobody else.
        """
        assert self.new.is_owned_by(self.com_admin)
        assert self.new.is_owned_by(self.author)
        assert not self.new.is_owned_by(self.anonymous)
        assert not self.new.is_owned_by(self.sli)

    def test_news_viewer(self):
        """Test that moderated news can be viewed by anyone
        and not moderated news only by com admins and by their author.
        """
        # by default news aren't moderated
        assert self.new.can_be_viewed_by(self.com_admin)
        assert self.new.can_be_viewed_by(self.author)
        assert not self.new.can_be_viewed_by(self.sli)
        assert not self.new.can_be_viewed_by(self.anonymous)

        self.new.is_moderated = True
        self.new.save()
        assert self.new.can_be_viewed_by(self.com_admin)
        assert self.new.can_be_viewed_by(self.sli)
        assert self.new.can_be_viewed_by(self.anonymous)
        assert self.new.can_be_viewed_by(self.author)

    def test_news_editor(self):
        """Test that only com admins and the original author can edit news."""
        assert self.new.can_be_edited_by(self.com_admin)
        assert self.new.can_be_edited_by(self.author)
        assert not self.new.can_be_edited_by(self.sli)
        assert not self.new.can_be_edited_by(self.anonymous)


class TestWeekmailArticle(TestCase):
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
        """Test that weekmails are owned only by com admins."""
        assert self.article.is_owned_by(self.com_admin)
        assert not self.article.is_owned_by(self.author)
        assert not self.article.is_owned_by(self.anonymous)
        assert not self.article.is_owned_by(self.sli)


class TestPoster(TestCase):
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
        """Test that poster are owned by com admins and board members in clubs."""
        assert self.poster.is_owned_by(self.com_admin)
        assert not self.poster.is_owned_by(self.anonymous)

        assert not self.poster.is_owned_by(self.susbcriber)
        assert self.poster.is_owned_by(self.sli)


class TestNewsCreation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = baker.make(Club)
        cls.user = subscriber_user.make()
        baker.make(Membership, user=cls.user, club=cls.club, role=5)

    def setUp(self):
        self.client.force_login(self.user)
        self.start = now() + timedelta(days=1)
        self.end = self.start + timedelta(hours=5)
        self.valid_payload = {
            "title": "Test news",
            "summary": "This is a test news",
            "content": "This is a test news",
            "club": self.club.pk,
            "is_weekly": False,
            "start_date": self.start,
            "end_date": self.end,
        }

    def test_create_news(self):
        response = self.client.post(reverse("com:news_new"), self.valid_payload)
        created = News.objects.order_by("id").last()
        assertRedirects(response, created.get_absolute_url())
        assert created.title == "Test news"
        assert not created.is_moderated
        dates = list(created.dates.values("start_date", "end_date"))
        assert dates == [{"start_date": self.start, "end_date": self.end}]

    def test_create_news_multiple_dates(self):
        self.valid_payload["is_weekly"] = True
        self.valid_payload["occurrences"] = 2
        response = self.client.post(reverse("com:news_new"), self.valid_payload)
        created = News.objects.order_by("id").last()

        assertRedirects(response, created.get_absolute_url())
        dates = list(
            created.dates.values("start_date", "end_date").order_by("start_date")
        )
        assert dates == [
            {"start_date": self.start, "end_date": self.end},
            {
                "start_date": self.start + timedelta(days=7),
                "end_date": self.end + timedelta(days=7),
            },
        ]

    def test_edit_news(self):
        news = baker.make(News, author=self.user, is_moderated=True)
        baker.make(
            NewsDate,
            news=news,
            start_date=self.start + timedelta(hours=1),
            end_date=self.end + timedelta(hours=1),
            _quantity=2,
        )

        response = self.client.post(
            reverse("com:news_edit", kwargs={"news_id": news.id}), self.valid_payload
        )
        created = News.objects.order_by("id").last()
        assertRedirects(response, created.get_absolute_url())
        assert created.title == "Test news"
        assert not created.is_moderated
        dates = list(created.dates.values("start_date", "end_date"))
        assert dates == [{"start_date": self.start, "end_date": self.end}]

    def test_ics_updated(self):
        """Test that the internal ICS is updated when news are created"""

        # we will just test that the ICS is modified.
        # Checking that the ICS is *well* modified is up to the ICS tests
        with patch("com.calendar.IcsCalendar.make_internal") as mocked:
            self.client.post(reverse("com:news_new"), self.valid_payload)
            mocked.assert_called()

        # The ICS file should also change after an update
        self.valid_payload["is_weekly"] = True
        self.valid_payload["occurrences"] = 2
        last_news = News.objects.order_by("id").last()

        with patch("com.calendar.IcsCalendar.make_internal") as mocked:
            self.client.post(
                reverse("com:news_edit", kwargs={"news_id": last_news.id}),
                self.valid_payload,
            )
            mocked.assert_called()


@pytest.mark.django_db
def test_feed(client):
    """Smoke test that checks that the atom feed is working"""
    resp = client.get(reverse("com:news_feed"))
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/rss+xml; charset=utf-8"
