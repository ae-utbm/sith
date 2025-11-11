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

from datetime import date, timedelta
from smtplib import SMTPException

import freezegun
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import View
from django.views.generic.base import ContextMixin
from model_bakery import baker
from pytest_django.asserts import assertInHTML, assertRedirects

from antispam.models import ToxicDomain
from club.models import Club, Membership
from core.markdown import markdown
from core.models import AnonymousUser, Group, Page, User, validate_promo
from core.utils import get_last_promo, get_semester_code, get_start_of_semester
from core.views import AllowFragment
from counter.models import Customer
from sith import settings


@pytest.mark.django_db
class TestUserRegistration:
    @pytest.fixture()
    def valid_payload(self):
        return {
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
            "first_name": "this user does not exist (yet)",
            "last_name": "this user does not exist (yet)",
            "email": "i-dont-exist-yet@git.an",
            "password1": "plop",
            "password2": "plop",
            "captcha_0": "dummy-value",
            "captcha_1": "PASSED",
        }

    @pytest.fixture()
    def scam_domains(self):
        return [baker.make(ToxicDomain, domain="scammer.spam")]

    def test_register_user_form_ok(self, client, valid_payload):
        """Should register a user correctly."""
        assert not User.objects.filter(email=valid_payload["email"]).exists()
        response = client.post(reverse("core:register"), valid_payload)
        assertRedirects(response, reverse("core:index"))
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Création de votre compte AE"
        assert User.objects.filter(email=valid_payload["email"]).exists()

    @pytest.mark.parametrize(
        ("payload_edit", "expected_error"),
        [
            (
                {"password2": "not the same as password1"},
                "Les deux mots de passe ne correspondent pas.",
            ),
            (
                {"email": "not-an-email"},
                "Saisissez une adresse de courriel valide.",
            ),
            (
                {"email": "not\\an@email.com"},
                "Saisissez une adresse de courriel valide.",
            ),
            (
                {"email": "legit@scammer.spam"},
                "Le domaine de l'addresse e-mail n'est pas autorisé.",
            ),
            ({"first_name": ""}, "Ce champ est obligatoire."),
            ({"last_name": ""}, "Ce champ est obligatoire."),
            ({"captcha_1": "WRONG_CAPTCHA"}, "CAPTCHA invalide"),
        ],
    )
    def test_register_user_form_fail(
        self, client, scam_domains, valid_payload, payload_edit, expected_error
    ):
        """Should not register a user correctly."""
        payload = valid_payload | payload_edit
        response = client.post(reverse("core:register"), payload)
        assert response.status_code == 200
        errors = BeautifulSoup(response.text, "lxml").find_all(class_="errorlist")
        assert len(errors) == 1
        assert errors[0].text == expected_error
        assert not User.objects.filter(email=payload["email"]).exists()

    def test_register_honeypot_fail(self, client: Client, valid_payload):
        payload = valid_payload | {
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE + "random"
        }
        response = client.post(reverse("core:register"), payload)
        assert response.status_code == 200
        assert not User.objects.filter(email=payload["email"]).exists()

    def test_register_user_form_fail_already_exists(
        self, client: Client, valid_payload
    ):
        """Should not register a user correctly if it already exists."""
        # create the user, then try to create it again
        client.post(reverse("core:register"), valid_payload)
        response = client.post(reverse("core:register"), valid_payload)

        assert response.status_code == 200
        error_html = (
            "<li>Un objet Utilisateur avec ce champ Adresse email existe déjà.</li>"
        )
        assertInHTML(error_html, str(response.text))

    def test_register_fail_with_not_existing_email(
        self, client: Client, valid_payload, monkeypatch
    ):
        """Test that, when email is valid but doesn't actually exist, registration fails."""

        def always_fail(*_args, **_kwargs):
            raise SMTPException

        monkeypatch.setattr(EmailMessage, "send", always_fail)

        response = client.post(reverse("core:register"), valid_payload)
        assert response.status_code == 200
        error_html = (
            "<li>Nous n'avons pas réussi à vérifier que cette adresse mail existe.</li>"
        )
        assertInHTML(error_html, str(response.text))


@pytest.mark.django_db
class TestUserLogin:
    @pytest.fixture()
    def user(self) -> User:
        return baker.make(User, password=make_password("plop"))

    @pytest.mark.parametrize(
        "identifier_getter",
        [
            lambda user: user.username,
            lambda user: user.email,
            lambda user: Customer.get_or_create(user)[0].account_id,
        ],
    )
    def test_login_fail(self, client, user, identifier_getter):
        """Should not login a user correctly."""
        identifier = identifier_getter(user)
        response = client.post(
            reverse("core:login"),
            {"username": identifier, "password": "wrong-password"},
        )
        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        soup = BeautifulSoup(response.text, "lxml")
        form = soup.find(id="login-form")
        assert (
            form.find(class_="alert alert-red").get_text(strip=True)
            == "Vos identifiants ne correspondent pas. Veuillez réessayer."
        )
        assert form.find("input", attrs={"name": "username"}).get("value") == identifier

    @pytest.mark.parametrize(
        "identifier_getter",
        [
            lambda user: user.username,
            lambda user: user.email,
            lambda user: Customer.get_or_create(user)[0].account_id,
        ],
    )
    def test_login_success(self, client, user, identifier_getter):
        """Should login a user correctly."""
        response = client.post(
            reverse("core:login"),
            {"username": identifier_getter(user), "password": "plop"},
        )
        assertRedirects(response, reverse("core:index"))
        assert response.wsgi_request.user == user


@pytest.mark.parametrize(
    ("md", "html"),
    [
        (
            "[nom du lien](page://nomDeLaPage)",
            '<a href="/page/nomDeLaPage/">nom du lien</a>',
        ),
        ("__texte__", "<u>texte</u>"),
        ("~~***__texte__***~~", "<del><em><strong><u>texte</u></strong></em></del>"),
        (
            '![tst_alt](/img.png?50% "tst_title")',
            '<img src="/img.png" alt="tst_alt" title="tst_title" style="width:50%;" />',
        ),
        (
            "[texte](page://tst-page)",
            '<a href="/page/tst-page/">texte</a>',
        ),
        (
            "![](/img.png?50x450)",
            '<img src="/img.png" alt="" style="width:50px;height:450px;" />',
        ),
        ("![](/img.png)", '<img src="/img.png" alt="" />'),
        (
            "![](/img.png?50%x120%)",
            '<img src="/img.png" alt="" style="width:50%;height:120%;" />',
        ),
        ("![](/img.png?50px)", '<img src="/img.png" alt="" style="width:50px;" />'),
        (
            "![](/img.png?50pxx120%)",
            '<img src="/img.png" alt="" style="width:50px;height:120%;" />',
        ),
        # when the image dimension has a wrong format, don't touch the url
        ("![](/img.png?50pxxxxxxxx)", '<img src="/img.png?50pxxxxxxxx" alt="" />'),
        ("![](/img.png?azerty)", '<img src="/img.png?azerty" alt="" />'),
    ],
)
def test_custom_markdown_syntax(md, html):
    """Test the homemade markdown syntax."""
    assert markdown(md) == f"<p>{html}</p>\n"


def test_full_markdown_syntax():
    syntax_path = settings.BASE_DIR / "core" / "fixtures"
    md = (syntax_path / "SYNTAX.md").read_text()
    html = (syntax_path / "SYNTAX.html").read_text()
    result = markdown(md)
    assert result == html


class TestPageHandling(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = baker.make(
            Group, permissions=[Permission.objects.get(codename="add_page")]
        )
        cls.user = baker.make(User, groups=[cls.group])

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_page_ok(self):
        """Should create a page correctly."""
        response = self.client.post(
            reverse("core:page_new"),
            {"parent": "", "name": "guy", "owner_group": self.group.id},
        )
        self.assertRedirects(
            response, reverse("core:page", kwargs={"page_name": "guy"})
        )
        assert Page.objects.filter(name="guy").exists()

        response = self.client.get(reverse("core:page", kwargs={"page_name": "guy"}))
        assert response.status_code == 200
        html = response.text
        assert '<a href="/page/guy/hist/">' in html
        assert '<a href="/page/guy/edit/">' in html
        assert '<a href="/page/guy/prop/">' in html

    def test_create_child_page_ok(self):
        """Should create a page correctly."""
        parent = baker.prepare(Page)
        parent.save(force_lock=True)
        response = self.client.get(
            reverse("core:page_new", query={"page": f"{parent._full_name}/new"})
        )

        assert response.status_code == 200
        # The name and parent inputs should be already filled
        soup = BeautifulSoup(response.text, "lxml")
        assert soup.find("input", {"name": "name"})["value"] == "new"
        select = soup.find("autocomplete-select", {"name": "parent"})
        assert select.find("option", {"selected": True})["value"] == str(parent.id)

        response = self.client.post(
            reverse("core:page_new"),
            {
                "parent": str(parent.id),
                "name": "new",
                "owner_group": str(self.group.id),
            },
        )
        new_url = reverse("core:page", kwargs={"page_name": f"{parent._full_name}/new"})
        assertRedirects(response, new_url, fetch_redirect_response=False)
        response = self.client.get(new_url)
        assert response.status_code == 200
        assert f'<a href="/page/{parent._full_name}/new/">' in response.text

    def test_access_child_page_ok(self):
        """Should display a page correctly."""
        parent = Page(name="guy", owner_group=self.group)
        parent.save(force_lock=True)
        page = Page(name="bibou", owner_group=self.group, parent=parent)
        page.save(force_lock=True)
        response = self.client.get(
            reverse("core:page", kwargs={"page_name": "guy/bibou"})
        )
        assert response.status_code == 200
        html = response.text
        self.assertIn('<a href="/page/guy/bibou/edit/">', html)

    def test_access_page_not_found(self):
        """Should not display a page correctly."""
        response = self.client.get(reverse("core:page", kwargs={"page_name": "swagg"}))
        assert response.status_code == 404
        assert '<a href="/page/create/?page=swagg">' in response.text

    def test_create_page_markdown_safe(self):
        """Should format the markdown and escape html correctly."""
        self.client.post(
            reverse("core:page_new"),
            {"parent": "", "name": "guy", "owner_group": self.group.id},
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
        assert response.status_code == 200
        expected = """
            <p>Guy <em>bibou</em></p>
            <p><a href="http://git.an">http://git.an</a></p>
            <h1>Swag</h1>
            <p>&lt;guy&gt;Bibou&lt;/guy&gt;</p>
            <p>&lt;script&gt;alert('Guy');&lt;/script&gt;</p>
            """
        assertInHTML(expected, response.text)


@pytest.mark.django_db
class TestUserTools:
    def test_anonymous_user_unauthorized(self, client):
        """An anonymous user shouldn't have access to the tools page."""
        url = reverse("core:user_tools")
        response = client.get(url)
        assertRedirects(
            response, expected_url=reverse("core:login", query={"next": url})
        )

    @pytest.mark.parametrize("username", ["guy", "root", "skia", "comunity"])
    def test_page_is_working(self, client, username):
        """All existing users should be able to see the test page."""
        # Test for simple user
        client.force_login(User.objects.get(username=username))
        response = client.get(reverse("core:user_tools"))
        assert response.status_code == 200


class TestUserIsInGroup(TestCase):
    """Test that the User.is_in_group() and AnonymousUser.is_in_group()
    work as intended.
    """

    @classmethod
    def setUpTestData(cls):
        cls.public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
        cls.public_user = baker.make(User)
        cls.club = baker.make(Club)

    def assert_in_public_group(self, user):
        assert user.is_in_group(pk=self.public_group.id)
        assert user.is_in_group(name=self.public_group.name)

    def assert_only_in_public_group(self, user):
        self.assert_in_public_group(user)
        for group in Group.objects.exclude(id=self.public_group.id):
            assert not user.is_in_group(pk=group.pk)
            assert not user.is_in_group(name=group.name)

    def test_anonymous_user(self):
        """Test that anonymous users are only in the public group."""
        user = AnonymousUser()
        self.assert_only_in_public_group(user)

    def test_not_subscribed_user(self):
        """Test that users who never subscribed are only in the public group."""
        self.assert_only_in_public_group(self.public_user)

    def test_wrong_parameter_fail(self):
        """Test that when neither the pk nor the name argument is given,
        the function raises a ValueError.
        """
        with self.assertRaises(ValueError):
            self.public_user.is_in_group()

    def test_number_queries(self):
        """Test that the number of db queries is stable
        and that less queries are made when making a new call.
        """
        group_in = baker.make(Group)
        self.public_user.groups.add(group_in)

        # clear the cached property `User.cached_groups`
        self.public_user.__dict__.pop("cached_groups", None)
        # Test when the user is in the group
        with self.assertNumQueries(1):
            self.public_user.is_in_group(pk=group_in.id)
        with self.assertNumQueries(0):
            self.public_user.is_in_group(pk=group_in.id)

        group_not_in = baker.make(Group)
        self.public_user.__dict__.pop("cached_groups", None)
        # Test when the user is not in the group
        with self.assertNumQueries(1):
            self.public_user.is_in_group(pk=group_not_in.id)
        with self.assertNumQueries(0):
            self.public_user.is_in_group(pk=group_not_in.id)

    def test_cache_properly_cleared_membership(self):
        """Test that when the membership of a user end,
        the cache is properly invalidated.
        """
        membership = baker.make(Membership, club=self.club, user=self.public_user)
        cache.clear()
        self.club.get_membership_for(self.public_user)  # this should populate the cache
        assert membership == cache.get(
            f"membership_{self.club.id}_{self.public_user.id}"
        )
        membership.end_date = now() - timedelta(minutes=5)
        membership.save()
        cached_membership = cache.get(
            f"membership_{self.club.id}_{self.public_user.id}"
        )
        assert cached_membership == "not_member"

    def test_not_existing_group(self):
        """Test that searching for a not existing group
        returns False.
        """
        user = baker.make(User)
        user.groups.set(list(Group.objects.all()))
        assert not user.is_in_group(name="This doesn't exist")


class TestDateUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autumn_month = settings.SITH_SEMESTER_START_AUTUMN[0]
        cls.autumn_day = settings.SITH_SEMESTER_START_AUTUMN[1]
        cls.spring_month = settings.SITH_SEMESTER_START_SPRING[0]
        cls.spring_day = settings.SITH_SEMESTER_START_SPRING[1]

        cls.autumn_semester_january = date(2025, 1, 4)
        cls.autumn_semester_september = date(2024, 9, 4)
        cls.autumn_first_day = date(2024, cls.autumn_month, cls.autumn_day)

        cls.spring_semester_march = date(2023, 3, 4)
        cls.spring_first_day = date(2023, cls.spring_month, cls.spring_day)

    def test_get_semester(self):
        """Test that the get_semester function returns the correct semester string."""
        assert get_semester_code(self.autumn_semester_january) == "A24"
        assert get_semester_code(self.autumn_semester_september) == "A24"
        assert get_semester_code(self.autumn_first_day) == "A24"

        assert get_semester_code(self.spring_semester_march) == "P23"
        assert get_semester_code(self.spring_first_day) == "P23"

    def test_get_start_of_semester_fixed_date(self):
        """Test that the get_start_of_semester correctly the starting date of the semester."""
        automn_2024 = date(2024, self.autumn_month, self.autumn_day)
        assert get_start_of_semester(self.autumn_semester_january) == automn_2024
        assert get_start_of_semester(self.autumn_semester_september) == automn_2024
        assert get_start_of_semester(self.autumn_first_day) == automn_2024

        spring_2023 = date(2023, self.spring_month, self.spring_day)
        assert get_start_of_semester(self.spring_semester_march) == spring_2023
        assert get_start_of_semester(self.spring_first_day) == spring_2023

    def test_get_start_of_semester_today(self):
        """Test that the get_start_of_semester returns the start of the current semester
        when no date is given.
        """
        with freezegun.freeze_time(self.autumn_semester_september):
            assert get_start_of_semester() == self.autumn_first_day

        with freezegun.freeze_time(self.spring_semester_march):
            assert get_start_of_semester() == self.spring_first_day

    def test_get_start_of_semester_changing_date(self):
        """Test that the get_start_of_semester correctly gives the starting date of the semester,
        even when the semester changes while the server isn't restarted.
        """
        spring_2023 = date(2023, self.spring_month, self.spring_day)
        autumn_2023 = date(2023, self.autumn_month, self.autumn_day)
        mid_spring = spring_2023 + timedelta(days=45)
        mid_autumn = autumn_2023 + timedelta(days=45)

        with freezegun.freeze_time(mid_spring) as frozen_time:
            assert get_start_of_semester() == spring_2023

            # forward time to the middle of the next semester
            frozen_time.move_to(mid_autumn)
            assert get_start_of_semester() == autumn_2023


@pytest.mark.parametrize(
    ("current_date", "promo"),
    [("2020-10-01", 22), ("2025-03-01", 26), ("2000-11-11", 2)],
)
def test_get_last_promo(current_date: str, promo: int):
    with freezegun.freeze_time(current_date):
        assert get_last_promo() == promo


@pytest.mark.parametrize("promo", [0, 24])
def test_promo_validator(promo: int):
    with freezegun.freeze_time("2021-10-01"), pytest.raises(ValidationError):
        validate_promo(promo)


def test_allow_fragment_mixin():
    class TestAllowFragmentView(AllowFragment, ContextMixin, View):
        def get(self, *args, **kwargs):
            context = self.get_context_data(**kwargs)
            return context["is_fragment"]

    request = RequestFactory().get("/test")
    base_headers = request.headers
    assert not TestAllowFragmentView.as_view()(request)
    request.headers = {"HX-Request": False, **base_headers}
    assert not TestAllowFragmentView.as_view()(request)
    request.headers = {"HX-Request": True, **base_headers}
    assert TestAllowFragmentView.as_view()(request)
