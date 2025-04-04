from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from club.forms import MailingForm
from club.models import Club, Mailing, Membership
from core.models import User


class TestMailingForm(TestCase):
    """Perform validation tests for MailingForm."""

    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        cls.rbatsbak = User.objects.get(username="rbatsbak")
        cls.krophil = User.objects.get(username="krophil")
        cls.comunity = User.objects.get(username="comunity")
        cls.root = User.objects.get(username="root")
        cls.club = Club.objects.get(id=settings.SITH_PDF_CLUB_ID)
        cls.mail_url = reverse("club:mailing", kwargs={"club_id": cls.club.id})
        Membership(
            user=cls.rbatsbak,
            club=cls.club,
            start_date=timezone.now(),
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
        ).save()

    def test_mailing_list_add_no_moderation(self):
        # Test with Communication admin
        self.client.force_login(self.comunity)
        response = self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "foyer"},
        )
        self.assertRedirects(response, self.mail_url)
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "Liste de diffusion foyer@utbm.fr" in response.content.decode()

        # Test with Root
        self.client.force_login(self.root)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "Liste de diffusion mde@utbm.fr" in response.content.decode()

    def test_mailing_list_add_moderation(self):
        self.client.force_login(self.rbatsbak)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Liste de diffusion mde@utbm.fr" not in content
        assert "<p>Listes de diffusions en attente de modération</p>" in content
        assert "<li>mde@utbm.fr" in content

    def test_mailing_list_forbidden(self):
        # With anonymous user
        response = self.client.get(self.mail_url)
        self.assertContains(response, "", status_code=403)

        # With user not in club
        self.client.force_login(self.krophil)
        response = self.client.get(self.mail_url)
        assert response.status_code == 403

    def test_add_new_subscription_fail_not_moderated(self):
        self.client.force_login(self.rbatsbak)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "skia@git.an" not in response.content.decode()

    def test_add_new_subscription_success(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Add single user
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        assert "skia@git.an" in response.content.decode()

        # Add multiple users
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": (self.comunity.id, self.rbatsbak.id),
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content

        # Add arbitrary email
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "arbitrary@git.an",
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content
        assert "arbitrary@git.an" in content

        # Add user and arbitrary email
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "more.arbitrary@git.an",
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "richard@git.an" in content
        assert "comunity@git.an" in content
        assert "skia@git.an" in content
        assert "arbitrary@git.an" in content
        assert "more.arbitrary@git.an" in content
        assert "krophil@git.an" in content

    def test_add_new_subscription_fail_form_errors(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Neither email or email is specified
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code
        self.assertInHTML(
            _("You must specify at least an user or an email address"),
            response.content.decode(),
        )

        # No mailing specified
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
            },
        )
        assert response.status_code == 200
        assert _("This field is required") in response.content.decode()

        # One of the selected users doesn't exist
        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": [789],
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("You must specify at least an user or an email address"),
            response.content.decode(),
        )

        # An user has no email address
        self.krophil.email = ""
        self.krophil.save()

        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("One of the selected users doesn't have an email address"),
            response.content.decode(),
        )

        self.krophil.email = "krophil@git.an"
        self.krophil.save()

        # An user is added twice

        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )

        response = self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        assert response.status_code == 200
        self.assertInHTML(
            _("This email is already suscribed in this mailing"),
            response.content.decode(),
        )

    def test_remove_subscription_success(self):
        # Prepare mailing list
        self.client.force_login(self.comunity)
        self.client.post(
            self.mail_url,
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        mde = Mailing.objects.get(email="mde")
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": (
                    self.comunity.id,
                    self.rbatsbak.id,
                    self.krophil.id,
                ),
                "subscription_mailing": mde.id,
            },
        )

        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" in content
        assert "richard@git.an" in content
        assert "krophil@git.an" in content

        # Delete one user
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d" % mde.id: mde.subscriptions.get(user=self.krophil).id,
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" in content
        assert "richard@git.an" in content
        assert "krophil@git.an" not in content

        # Delete multiple users
        self.client.post(
            self.mail_url,
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d" % mde.id: [
                    user.id
                    for user in mde.subscriptions.filter(
                        user__in=[self.rbatsbak, self.comunity]
                    ).all()
                ],
            },
        )
        response = self.client.get(self.mail_url)
        assert response.status_code == 200
        content = response.content.decode()

        assert "comunity@git.an" not in content
        assert "richard@git.an" not in content
        assert "krophil@git.an" not in content
