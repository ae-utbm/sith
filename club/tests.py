# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.conf import settings
from django.test import TestCase
from django.utils import timezone, html
from django.utils.translation import gettext as _
from django.urls import reverse
from django.core.management import call_command
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

from core.models import User
from club.models import Club, Membership, Mailing
from club.forms import MailingForm
from sith.settings import SITH_BAR_MANAGER


# Create your tests here.


class ClubTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.rbatsbak = User.objects.filter(username="rbatsbak").first()
        self.guy = User.objects.filter(username="guy").first()
        self.bdf = Club.objects.filter(unix_name=SITH_BAR_MANAGER["unix_name"]).first()

    def test_create_add_user_to_club_from_root_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 3},
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in str(response.content)
        )

    def test_create_add_multiple_user_to_club_from_root_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {
                "users": "|%d|%d|" % (self.skia.id, self.rbatsbak.id),
                "start_date": "12/06/2016",
                "role": 3,
            },
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertTrue(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in content
        )
        self.assertTrue(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in content
        )

    def test_create_add_user_to_club_from_root_fail_not_subscriber(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.guy.id, "start_date": "12/06/2016", "role": 3},
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<ul class="errorlist"><li>' in str(response.content))
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertFalse(
            "Guy Carlier</a></td>\\n                    <td>Responsable info</td>"
            in str(response.content)
        )

    def test_create_add_user_to_club_from_root_fail_already_in_club(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 3},
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in str(response.content)
        )
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 4},
        )
        self.assertTrue(response.status_code == 200)
        self.assertFalse(
            "S&#39; Kia</a></td>\\n                <td>Secrétaire</td>"
            in str(response.content)
        )

    def test_create_add_user_non_existent_to_club_from_root_fail(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": [9999], "start_date": "12/06/2016", "role": 3},
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertTrue('<ul class="errorlist"><li>' in content)
        self.assertFalse("<td>Responsable info</td>" in content)
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {
                "users": "|%d|%d|" % (self.skia.id, 9999),
                "start_date": "12/06/2016",
                "role": 3,
            },
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertTrue('<ul class="errorlist"><li>' in content)
        self.assertFalse("<td>Responsable info</td>" in content)

    def test_create_add_user_to_club_from_skia_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 10},
        )
        self.client.login(username="skia", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.rbatsbak.id, "start_date": "12/06/2016", "role": 9},
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            """Richard Batsbak</a></td>\n                    <td>Vice-Président⸱e</td>""",
            response.content.decode(),
        )

    def test_create_add_user_to_club_from_richard_fail(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.rbatsbak.id, "start_date": "12/06/2016", "role": 3},
        )
        self.client.login(username="rbatsbak", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 10},
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue(
            "<li>Vous n&#x27;avez pas la permission de faire cela</li>"
            in str(response.content)
        )

    def test_role_required_if_users_specified(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.rbatsbak.id, "start_date": "12/06/2016"},
        )
        self.assertTrue(
            '<ul class="errorlist"><li>Vous devez choisir un r' in str(response.content)
        )

    def test_mark_old_user_to_club_from_skia_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {
                "users": "|%d|%d|" % (self.skia.id, self.rbatsbak.id),
                "start_date": "12/06/2016",
                "role": 3,
            },
        )
        self.client.login(username="skia", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.rbatsbak.id},
        )
        self.assertTrue(response.status_code == 302)

        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertFalse(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in content
        )
        self.assertTrue(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in content
        )

        # Skia is board member so he should be able to mark as old even without being in the club
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.skia.id},
        )
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.rbatsbak.id, "start_date": "12/06/2016", "role": 3},
        )
        self.client.login(username="skia", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.rbatsbak.id},
        )
        self.assertFalse(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in str(response.content)
        )

    def test_mark_old_multiple_users_from_skia_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {
                "users": "|%d|%d|" % (self.skia.id, self.rbatsbak.id),
                "start_date": "12/06/2016",
                "role": 3,
            },
        )
        self.client.login(username="skia", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": [self.rbatsbak.id, self.skia.id]},
        )
        self.assertTrue(response.status_code == 302)

        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertFalse(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in content
        )
        self.assertFalse(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in content
        )

    def test_mark_old_user_to_club_from_richard_ok(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {
                "users": "|%d|%d|" % (self.skia.id, self.rbatsbak.id),
                "start_date": "12/06/2016",
                "role": 3,
            },
        )

        # Test with equal rights
        self.client.login(username="rbatsbak", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.skia.id},
        )
        self.assertTrue(response.status_code == 302)

        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertTrue(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in content
        )
        self.assertFalse(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in content
        )

        # Test with lower rights
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 0},
        )

        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.skia.id},
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        content = str(response.content)
        self.assertTrue(
            "Richard Batsbak</a></td>\\n                    <td>Responsable info</td>"
            in content
        )
        self.assertFalse(
            "S&#39; Kia</a></td>\\n                    <td>Curieux</td>" in content
        )

    def test_mark_old_user_to_club_from_richard_fail(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.skia.id, "start_date": "12/06/2016", "role": 3},
        )

        # Test with richard outside of the club
        self.client.login(username="rbatsbak", password="plop")
        response = self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.skia.id},
        )
        self.assertTrue(response.status_code == 200)

        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertTrue(response.status_code == 200)
        self.assertTrue(
            "S&#39; Kia</a></td>\\n                    <td>Responsable info</td>"
            in str(response.content)
        )

        # Test with lower rights
        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users": self.rbatsbak.id, "start_date": "12/06/2016", "role": 0},
        )

        self.client.post(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id}),
            {"users_old": self.skia.id},
        )
        response = self.client.get(
            reverse("club:club_members", kwargs={"club_id": self.bdf.id})
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(
            "Richard Batsbak</a></td>\n                    <td>Curieux⸱euse</td>",
            content,
        )
        self.assertIn(
            "S&#39; Kia</a></td>\n                    <td>Responsable info</td>",
            content,
        )


class MailingFormTest(TestCase):
    """Perform validation tests for MailingForm"""

    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.rbatsbak = User.objects.filter(username="rbatsbak").first()
        self.krophil = User.objects.filter(username="krophil").first()
        self.comunity = User.objects.filter(username="comunity").first()
        self.bdf = Club.objects.filter(unix_name=SITH_BAR_MANAGER["unix_name"]).first()
        Membership(
            user=self.rbatsbak,
            club=self.bdf,
            start_date=timezone.now(),
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
        ).save()

    def test_mailing_list_add_no_moderation(self):
        # Test with Communication admin
        self.client.login(username="comunity", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "foyer"},
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, text="Liste de diffusion foyer@utbm.fr")

        # Test with Root
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, text="Liste de diffusion mde@utbm.fr")

    def test_mailing_list_add_moderation(self):
        self.client.login(username="rbatsbak", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertNotContains(response, text="Liste de diffusion mde@utbm.fr")
        self.assertContains(
            response, text="<p>Listes de diffusions en attente de modération</p>"
        )
        self.assertContains(response, "<li>mde@utbm.fr")

    def test_mailing_list_forbidden(self):
        # With anonymous user
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "", status_code=403)

        # With user not in club
        self.client.login(username="krophil", password="plop")
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "", status_code=403)

    def test_add_new_subscription_fail_not_moderated(self):
        self.client.login(username="rbatsbak", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertNotContains(response, "skia@git.an")

    def test_add_new_subscription_success(self):
        # Prepare mailing list
        self.client.login(username="comunity", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Add single user
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.skia.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "skia@git.an")

        # Add multiple users
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|%s|%s|" % (self.comunity.id, self.rbatsbak.id),
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "richard@git.an")
        self.assertContains(response, "comunity@git.an")
        self.assertContains(response, "skia@git.an")

        # Add arbitrary email
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "arbitrary@git.an",
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "richard@git.an")
        self.assertContains(response, "comunity@git.an")
        self.assertContains(response, "skia@git.an")
        self.assertContains(response, "arbitrary@git.an")

        # Add user and arbitrary email
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_email": "more.arbitrary@git.an",
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )
        self.assertContains(response, "richard@git.an")
        self.assertContains(response, "comunity@git.an")
        self.assertContains(response, "skia@git.an")
        self.assertContains(response, "arbitrary@git.an")
        self.assertContains(response, "more.arbitrary@git.an")
        self.assertContains(response, "krophil@git.an")

    def test_add_new_subscription_fail_form_errors(self):
        # Prepare mailing list
        self.client.login(username="comunity", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )

        # Neither email or email is specified
        response = self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        self.assertContains(
            response, text=_("You must specify at least an user or an email address")
        )

        # No mailing specified
        response = self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
            },
        )
        self.assertContains(response, text=_("This field is required"))

        # One of the selected users doesn't exist
        response = self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|789|",
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        self.assertContains(
            response, text=html.escape(_("One of the selected users doesn't exist"))
        )

        # An user has no email adress
        self.krophil.email = ""
        self.krophil.save()

        response = self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        self.assertContains(
            response,
            text=html.escape(
                _("One of the selected users doesn't have an email address")
            ),
        )

        self.krophil.email = "krophil@git.an"
        self.krophil.save()

        # An user is added twice

        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )

        response = self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": self.krophil.id,
                "subscription_mailing": Mailing.objects.get(email="mde").id,
            },
        )
        self.assertContains(
            response,
            text=html.escape(_("This email is already suscribed in this mailing")),
        )

    def test_remove_subscription_success(self):
        # Prepare mailing list
        self.client.login(username="comunity", password="plop")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {"action": MailingForm.ACTION_NEW_MAILING, "mailing_email": "mde"},
        )
        mde = Mailing.objects.get(email="mde")
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_NEW_SUBSCRIPTION,
                "subscription_users": "|%s|%s|%s|"
                % (self.comunity.id, self.rbatsbak.id, self.krophil.id),
                "subscription_mailing": mde.id,
            },
        )

        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )

        self.assertContains(response, "comunity@git.an")
        self.assertContains(response, "richard@git.an")
        self.assertContains(response, "krophil@git.an")

        # Delete one user
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d" % mde.id: mde.subscriptions.get(user=self.krophil).id,
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )

        self.assertContains(response, "comunity@git.an")
        self.assertContains(response, "richard@git.an")
        self.assertNotContains(response, "krophil@git.an")

        # Delete multiple users
        self.client.post(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id}),
            {
                "action": MailingForm.ACTION_REMOVE_SUBSCRIPTION,
                "removal_%d"
                % mde.id: [
                    user.id
                    for user in mde.subscriptions.filter(
                        user__in=[self.rbatsbak, self.comunity]
                    ).all()
                ],
            },
        )
        response = self.client.get(
            reverse("club:mailing", kwargs={"club_id": self.bdf.id})
        )

        self.assertNotContains(response, "comunity@git.an")
        self.assertNotContains(response, "richard@git.an")
        self.assertNotContains(response, "krophil@git.an")


class ClubSellingViewTest(TestCase):
    """
    Perform basics tests to ensure that the page is available
    """

    def setUp(self):
        call_command("populate")
        self.ae = Club.objects.filter(unix_name="ae").first()

    def test_page_not_internal_error(self):
        """
        Test that the page does not return and internal error
        """
        self.client.login(username="skia", password="plop")
        response = self.client.get(
            reverse("club:club_sellings", kwargs={"club_id": self.ae.id})
        )
        self.assertFalse(response.status_code == 500)
