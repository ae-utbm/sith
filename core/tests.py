# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import os
from datetime import date, timedelta

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.core.management import call_command
from django.utils.timezone import now

from club.models import Membership
from core.models import User, Group, Page, AnonymousUser
from core.markdown import markdown
from core.utils import get_start_of_semester
from sith import settings

"""
to run these tests :
    python3 manage.py test
"""


class UserRegistrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.all().delete()

    def test_register_user_form_ok(self):
        """
        Should register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "guy@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_OK" in str(response.content))

    def test_register_user_form_fail_password(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop2",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_email(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "bibou.git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_missing_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_missing_date_of_birth(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_missing_first_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_wrong_captcha(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Bibou",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "WRONG_CAPTCHA",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_register_user_form_fail_already_exists(self):
        """
        Should not register a user correctly
        """
        c = Client()
        c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        response = c.post(
            reverse("core:register"),
            {
                "first_name": "Bibou",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("TEST_REGISTER_USER_FORM_FAIL" in str(response.content))

    def test_login_success(self):
        """
        Should login a user correctly
        """
        c = Client()
        c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        response = c.post(
            reverse("core:login"), {"username": "gcarlier", "password": "plop"}
        )
        self.assertTrue(response.status_code == 302)
        # self.assertTrue('Hello, world' in str(response.content))

    def test_login_fail(self):
        """
        Should not login a user correctly
        """
        c = Client()
        c.post(
            reverse("core:register"),
            {
                "first_name": "Guy",
                "last_name": "Carlier",
                "email": "bibou@git.an",
                "date_of_birth": "12/6/1942",
                "password1": "plop",
                "password2": "plop",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED",
            },
        )
        response = c.post(
            reverse("core:login"), {"username": "gcarlier", "password": "guy"}
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue(
            """<p class="alert alert-red">Votre nom d\\'utilisateur et votre mot de passe ne correspondent pas. Merci de r\\xc3\\xa9essayer.</p>"""
            in str(response.content)
        )


class MarkdownTest(TestCase):
    def test_full_markdown_syntax(self):
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root_path) + "/doc/SYNTAX.md", "r") as md_file:
            md = md_file.read()
        with open(os.path.join(root_path) + "/doc/SYNTAX.html", "r") as html_file:
            html = html_file.read()
        result = markdown(md)
        self.assertTrue(result == html)


class PageHandlingTest(TestCase):
    def setUp(self):
        self.client.login(username="root", password="plop")
        self.root_group = Group.objects.get(name="Root")

    def test_create_page_ok(self):
        """
        Should create a page correctly
        """

        response = self.client.post(
            reverse("core:page_new"),
            {"parent": "", "name": "guy", "owner_group": self.root_group.id},
        )
        self.assertRedirects(
            response, reverse("core:page", kwargs={"page_name": "guy"})
        )
        self.assertTrue(Page.objects.filter(name="guy").exists())

        response = self.client.get(reverse("core:page", kwargs={"page_name": "guy"}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<a href="/page/guy/hist/">', html)
        self.assertIn('<a href="/page/guy/edit/">', html)
        self.assertIn('<a href="/page/guy/prop/">', html)

    def test_create_child_page_ok(self):
        """
        Should create a page correctly
        """
        # remove all other pages to make sure there is no side effect
        Page.objects.all().delete()
        self.client.post(
            reverse("core:page_new"),
            {"parent": "", "name": "guy", "owner_group": str(self.root_group.id)},
        )
        page = Page.objects.first()
        response = self.client.post(
            reverse("core:page_new"),
            {
                "parent": str(page.id),
                "name": "bibou",
                "owner_group": str(self.root_group.id),
            },
        )
        response = self.client.get(
            reverse("core:page", kwargs={"page_name": "guy/bibou"})
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<a href="/page/guy/bibou/">' in str(response.content))

    def test_access_child_page_ok(self):
        """
        Should display a page correctly
        """
        parent = Page(name="guy", owner_group=self.root_group)
        parent.save(force_lock=True)
        page = Page(name="bibou", owner_group=self.root_group, parent=parent)
        page.save(force_lock=True)
        response = self.client.get(
            reverse("core:page", kwargs={"page_name": "guy/bibou"})
        )
        self.assertTrue(response.status_code == 200)
        html = response.content.decode()
        self.assertIn('<a href="/page/guy/bibou/edit/">', html)

    def test_access_page_not_found(self):
        """
        Should not display a page correctly
        """
        response = self.client.get(reverse("core:page", kwargs={"page_name": "swagg"}))
        self.assertTrue(response.status_code == 200)
        html = response.content.decode()
        self.assertIn('<a href="/page/create/?page=swagg">', html)

    def test_create_page_markdown_safe(self):
        """
        Should format the markdown and escape html correctly
        """
        self.client.post(
            reverse("core:page_new"), {"parent": "", "name": "guy", "owner_group": "1"}
        )
        self.client.post(
            reverse("core:page_edit", kwargs={"page_name": "guy"}),
            {
                "title": "Bibou",
                "content": """Guy *bibou*

http://git.an

# Swag

<guy>Bibou</guy>

<script>alert('Guy');</script>
""",
            },
        )
        response = self.client.get(reverse("core:page", kwargs={"page_name": "guy"}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(
            '<p>Guy <em>bibou</em></p>\\n<p><a href="http://git.an">http://git.an</a></p>\\n'
            + "<h1>Swag</h1>\\n&lt;guy&gt;Bibou&lt;/guy&gt;"
            + "&lt;script&gt;alert(\\'Guy\\');&lt;/script&gt;"
            in str(response.content)
        )


class UserToolsTest(TestCase):
    def test_anonymous_user_unauthorized(self):
        response = self.client.get(reverse("core:user_tools"))
        self.assertEqual(response.status_code, 403)

    def test_page_is_working(self):
        # Test for simple user
        self.client.login(username="guy", password="plop")
        response = self.client.get(reverse("core:user_tools"))
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 200)

        # Test for root
        self.client.login(username="root", password="plop")
        response = self.client.get(reverse("core:user_tools"))
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 200)

        # Test for skia
        self.client.login(username="skia", password="plop")
        response = self.client.get(reverse("core:user_tools"))
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 200)

        # Test for comunity
        self.client.login(username="comunity", password="plop")
        response = self.client.get(reverse("core:user_tools"))
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 200)


# TODO: many tests on the pages:
#   - renaming a page
#   - changing a page's parent --> check that page's children's full_name
#   - changing the different groups of the page


class FileHandlingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.subscriber = User.objects.get(username="subscriber")

    def setUp(self):
        self.client.login(username="subscriber", password="plop")

    def test_create_folder_home(self):
        response = self.client.post(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}),
            {"folder_name": "GUY_folder_test"},
        )
        self.assertTrue(response.status_code == 302)
        response = self.client.get(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id})
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("GUY_folder_test</a>" in str(response.content))

    def test_upload_file_home(self):
        with open("/bin/ls", "rb") as f:
            response = self.client.post(
                reverse(
                    "core:file_detail", kwargs={"file_id": self.subscriber.home.id}
                ),
                {"file_field": f},
            )
        self.assertTrue(response.status_code == 302)
        response = self.client.get(
            reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id})
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue("ls</a>" in str(response.content))


class UserIsInGroupTest(TestCase):
    """
    Test that the User.is_in_group() and AnonymousUser.is_in_group()
    work as intended
    """

    @classmethod
    def setUpTestData(cls):
        from club.models import Club

        cls.root_group = Group.objects.get(name="Root")
        cls.public = Group.objects.get(name="Public")
        cls.subscribers = Group.objects.get(name="Subscribers")
        cls.old_subscribers = Group.objects.get(name="Old subscribers")
        cls.accounting_admin = Group.objects.get(name="Accounting admin")
        cls.com_admin = Group.objects.get(name="Communication admin")
        cls.counter_admin = Group.objects.get(name="Counter admin")
        cls.banned_alcohol = Group.objects.get(name="Banned from buying alcohol")
        cls.banned_counters = Group.objects.get(name="Banned from counters")
        cls.banned_subscription = Group.objects.get(name="Banned to subscribe")
        cls.sas_admin = Group.objects.get(name="SAS admin")
        cls.club = Club.objects.create(
            name="Fake Club",
            unix_name="fake-club",
            address="Fake address",
        )
        cls.main_club = Club.objects.get(id=1)

    def setUp(self) -> None:
        self.toto = User.objects.create(
            username="toto", first_name="a", last_name="b", email="a.b@toto.fr"
        )
        self.skia = User.objects.get(username="skia")

    def assert_in_public_group(self, user):
        self.assertTrue(user.is_in_group(pk=self.public.id))
        self.assertTrue(user.is_in_group(name=self.public.name))

    def assert_in_club_metagroups(self, user, club):
        meta_groups_board = club.unix_name + settings.SITH_BOARD_SUFFIX
        meta_groups_members = club.unix_name + settings.SITH_MEMBER_SUFFIX
        self.assertFalse(user.is_in_group(name=meta_groups_board))
        self.assertFalse(user.is_in_group(name=meta_groups_members))

    def assert_only_in_public_group(self, user):
        self.assert_in_public_group(user)
        for group in (
            self.root_group,
            self.banned_counters,
            self.accounting_admin,
            self.sas_admin,
            self.subscribers,
            self.old_subscribers,
        ):
            self.assertFalse(user.is_in_group(pk=group.pk))
            self.assertFalse(user.is_in_group(name=group.name))
        meta_groups_board = self.club.unix_name + settings.SITH_BOARD_SUFFIX
        meta_groups_members = self.club.unix_name + settings.SITH_MEMBER_SUFFIX
        self.assertFalse(user.is_in_group(name=meta_groups_board))
        self.assertFalse(user.is_in_group(name=meta_groups_members))

    def test_anonymous_user(self):
        """
        Test that anonymous users are only in the public group
        """
        user = AnonymousUser()
        self.assert_only_in_public_group(user)

    def test_not_subscribed_user(self):
        """
        Test that users who never subscribed are only in the public group
        """
        self.assert_only_in_public_group(self.toto)

    def test_wrong_parameter_fail(self):
        """
        Test that when neither the pk nor the name argument is given,
        the function raises a ValueError
        """
        with self.assertRaises(ValueError):
            self.toto.is_in_group()

    def test_number_queries(self):
        """
        Test that the number of db queries is stable
        and that less queries are made when making a new call
        """
        # make sure Skia is in at least one group
        self.skia.groups.add(Group.objects.first().pk)
        skia_groups = self.skia.groups.all()

        group_in = skia_groups.first()
        cache.clear()
        # Test when the user is in the group
        with self.assertNumQueries(2):
            self.skia.is_in_group(pk=group_in.id)
        with self.assertNumQueries(0):
            self.skia.is_in_group(pk=group_in.id)

        ids = skia_groups.values_list("pk", flat=True)
        group_not_in = Group.objects.exclude(pk__in=ids).first()
        cache.clear()
        # Test when the user is not in the group
        with self.assertNumQueries(2):
            self.skia.is_in_group(pk=group_not_in.id)
        with self.assertNumQueries(0):
            self.skia.is_in_group(pk=group_not_in.id)

    def test_cache_properly_cleared_membership(self):
        """
        Test that when the membership of a user end,
        the cache is properly invalidated
        """
        membership = Membership.objects.create(
            club=self.club, user=self.toto, end_date=None
        )
        meta_groups_members = self.club.unix_name + settings.SITH_MEMBER_SUFFIX
        cache.clear()
        self.assertTrue(self.toto.is_in_group(name=meta_groups_members))
        self.assertEqual(
            membership, cache.get(f"membership_{self.club.id}_{self.toto.id}")
        )
        membership.end_date = now() - timedelta(minutes=5)
        membership.save()
        cached_membership = cache.get(f"membership_{self.club.id}_{self.toto.id}")
        self.assertEqual(cached_membership, "not_member")
        self.assertFalse(self.toto.is_in_group(name=meta_groups_members))

    def test_cache_properly_cleared_group(self):
        """
        Test that when a user is removed from a group,
        the is_in_group_method return False when calling it again
        """
        # testing with pk
        self.toto.groups.add(self.com_admin.pk)
        self.assertTrue(self.toto.is_in_group(pk=self.com_admin.pk))

        self.toto.groups.remove(self.com_admin.pk)
        self.assertFalse(self.toto.is_in_group(pk=self.com_admin.pk))

        # testing with name
        self.toto.groups.add(self.sas_admin.pk)
        self.assertTrue(self.toto.is_in_group(name="SAS admin"))

        self.toto.groups.remove(self.sas_admin.pk)
        self.assertFalse(self.toto.is_in_group(name="SAS admin"))

    def test_not_existing_group(self):
        """
        Test that searching for a not existing group
        returns False
        """
        self.assertFalse(self.skia.is_in_group(name="This doesn't exist"))


class UtilsTest(TestCase):
    def test_get_start_of_semester(self):
        autumn_month, autumn_day = settings.SITH_SEMESTER_START_AUTUMN
        spring_month, spring_day = settings.SITH_SEMESTER_START_SPRING

        t1_autumn_day = date(2025, 1, 4)  # between 1st January and 15 February
        t2_autumn_day = date(2024, 9, 1)  # between 15 August and 31 December
        t3_autumn_day = date(2024, autumn_month, autumn_day)  # on 15 August

        t1_spring_day = date(2023, 3, 1)  # between 15 February and 15 August
        t2_spring_day = date(2023, spring_month, spring_day)  # on 15 February

        self.assertEqual(
            get_start_of_semester(t1_autumn_day), date(2024, autumn_month, autumn_day)
        )
        self.assertEqual(
            get_start_of_semester(t2_autumn_day), date(2024, autumn_month, autumn_day)
        )
        self.assertEqual(
            get_start_of_semester(t3_autumn_day), date(2024, autumn_month, autumn_day)
        )
        self.assertEqual(
            get_start_of_semester(t1_spring_day), date(2023, spring_month, spring_day)
        )
        self.assertEqual(
            get_start_of_semester(t2_spring_day), date(2023, spring_month, spring_day)
        )
