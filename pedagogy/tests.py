# -*- coding:utf-8 -*
#
# Copyright 2019
# - Sli <antoine@bartuccio.fr>
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

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User

from pedagogy.models import UV, UVComment


def create_uv_template(user_id, code="IFC1", exclude_list=[]):
    """
    Factory to help UV creation/update in post requests
    """
    uv = {
        "code": code,
        "author": user_id,
        "credit_type": "TM",
        "semester": "SPRING",
        "language": "FR",
        "credits": 3,
        "hours_CM": 10,
        "hours_TD": 28,
        "hours_TP": 0,
        "hours_THE": 37,
        "hours_TE": 0,
        "manager": "Gilles BERTRAND",
        "title": "Algorithmique et programmation : niveau I, initiés - partie I",
        "objectives": """* Introduction à l'algorithmique et à la programmation pour initiés.
* Pratiques et développement en langage C.""",
        "program": """* Découverte des outils élémentaires utilisés pour écrire, compiler et exécuter un programme écrit en langage C
* Règles de programmation : normes en cours, règles de présentation du code, commentaires
* Initiation à l'algorithmique et découverte des bases du langage C :
    * les conditions
    * les boucles
    * les types de données
    * les tableaux à une dimension
    * manipulations des chaînes de caractères
    * les fonctions et procédures""",
        "skills": "* D'écrire un algorithme et de l'implémenter en C",
        "key_concepts": """* Algorithme
* Variables scalaires et vectorielles
* Structures alternatives, répétitives
* Fonctions, procédures
* Chaînes de caractères""",
    }
    for excluded in exclude_list:
        uv.pop(excluded)
    return uv


# UV class tests


class UVCreation(TestCase):
    """
    Test uv creation
    """

    def setUp(self):
        call_command("populate")
        self.bibou = User.objects.filter(username="root").first()
        self.tutu = User.objects.filter(username="tutu").first()
        self.sli = User.objects.filter(username="sli").first()
        self.guy = User.objects.filter(username="guy").first()

    def test_create_uv_admin_success(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(self.bibou.id)
        )
        self.assertEquals(response.status_code, 302)
        self.assertTrue(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(self.tutu.id)
        )
        self.assertEquals(response.status_code, 302)
        self.assertTrue(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_unauthorized_fail(self):
        # Test with anonymous user
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(0)
        )
        self.assertEquals(response.status_code, 403)

        # Test with subscribed user
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(self.sli.id)
        )
        self.assertEquals(response.status_code, 403)

        # Test with non subscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(self.guy.id)
        )
        self.assertEquals(response.status_code, 403)

        # Check that the UV has never been created
        self.assertFalse(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_bad_request_fail(self):
        self.client.login(username="tutu", password="plop")

        # Test with wrong user id (if someone cheats on the hidden input)
        response = self.client.post(
            reverse("pedagogy:uv_create"), create_uv_template(self.bibou.id)
        )
        self.assertNotEquals(response.status_code, 302)
        self.assertEquals(response.status_code, 200)

        # Remove a required field
        response = self.client.post(
            reverse("pedagogy:uv_create"),
            create_uv_template(self.tutu.id, exclude_list=["title"]),
        )
        self.assertNotEquals(response.status_code, 302)
        self.assertEquals(response.status_code, 200)

        # Check that the UV hase never been created
        self.assertFalse(UV.objects.filter(code="IFC1").exists())


class UVListTest(TestCase):
    """
    Test guide display rights
    """

    def setUp(self):
        call_command("populate")

    def test_uv_list_display_success(self):
        # Display for root
        self.client.login(username="root", password="plop")
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

        # Display for pedagogy admin
        self.client.login(username="tutu", password="plop")
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

        # Display for simple subscriber
        self.client.login(username="sli", password="plop")
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

    def test_uv_list_display_fail(self):
        # Don't display for anonymous user
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertEquals(response.status_code, 403)

        # Don't display for none subscribed users
        self.client.login(username="guy", password="plop")
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertEquals(response.status_code, 403)


class UVDeleteTest(TestCase):
    """
    Test UV deletion rights
    """

    def setUp(self):
        call_command("populate")

    def test_uv_delete_root_success(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse(
                "pedagogy:uv_delete", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            )
        )
        self.assertFalse(UV.objects.filter(code="PA00").exists())

    def test_uv_delete_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        self.client.post(
            reverse(
                "pedagogy:uv_delete", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            )
        )
        self.assertFalse(UV.objects.filter(code="PA00").exists())

    def test_uv_delete_pedagogy_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(
            reverse(
                "pedagogy:uv_delete", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            )
        )
        self.assertEquals(response.status_code, 403)

        # Not subscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse(
                "pedagogy:uv_delete", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            )
        )
        self.assertEquals(response.status_code, 403)

        # Simply subscribed user
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse(
                "pedagogy:uv_delete", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            )
        )
        self.assertEquals(response.status_code, 403)

        # Check that the UV still exists
        self.assertTrue(UV.objects.filter(code="PA00").exists())


class UVUpdateTest(TestCase):
    """
    Test UV update rights
    """

    def setUp(self):
        call_command("populate")
        self.bibou = User.objects.filter(username="root").first()
        self.tutu = User.objects.filter(username="tutu").first()
        self.sli = User.objects.filter(username="sli").first()
        self.guy = User.objects.filter(username="guy").first()

    def test_uv_update_root_success(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse(
                "pedagogy:uv_update", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            ),
            create_uv_template(self.bibou.id, code="PA00"),
        )
        self.assertEquals(UV.objects.get(code="PA00").credit_type, "TM")

    def test_uv_update_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        self.client.post(
            reverse(
                "pedagogy:uv_update", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            ),
            create_uv_template(self.tutu.id, code="PA00"),
        )
        self.assertEquals(UV.objects.get(code="PA00").credit_type, "TM")

    def test_uv_update_pedagogy_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(
            reverse(
                "pedagogy:uv_update", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            ),
            create_uv_template(0, code="PA00"),
        )
        self.assertEquals(response.status_code, 403)

        # Not subscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse(
                "pedagogy:uv_update", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            ),
            create_uv_template(self.guy.id, code="PA00"),
        )
        self.assertEquals(response.status_code, 403)

        # Simply subscribed user
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse(
                "pedagogy:uv_update", kwargs={"uv_id": UV.objects.get(code="PA00").id}
            ),
            create_uv_template(self.sli.id, code="PA00"),
        )
        self.assertEquals(response.status_code, 403)

        # Check that the UV has not changed
        self.assertEquals(UV.objects.get(code="PA00").credit_type, "OM")


# UVComment class tests


def create_uv_comment_template(user_id, uv_code="PA00", exclude_list=[]):
    """
    Factory to help UVComment creation/update in post requests
    """
    comment = {
        "author": user_id,
        "uv": UV.objects.get(code=uv_code).id,
        "grade_global": 5,
        "grade_utility": 5,
        "grade_interest": 5,
        "grade_teaching": -1,
        "grade_work_load": 3,
        "comment": "Superbe UV qui fait vivre la vie associative de l'école",
    }
    for excluded in exclude_list:
        comment.pop(excluded)
    return comment


class UVCommentCreationAndDisplay(TestCase):
    """
    Test UVComment creation and it's display
    Display and creation are the same view
    """

    def setUp(self):
        call_command("populate")
        self.bibou = User.objects.filter(username="root").first()
        self.tutu = User.objects.filter(username="tutu").first()
        self.sli = User.objects.filter(username="sli").first()
        self.guy = User.objects.filter(username="guy").first()
        self.uv = UV.objects.get(code="PA00")

    def test_create_uv_comment_admin_success(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(self.bibou.id),
        )
        self.assertEquals(response.status_code, 302)
        response = self.client.get(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id})
        )
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(self.tutu.id),
        )
        self.assertEquals(response.status_code, 302)
        response = self.client.get(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id})
        )
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_subscriber_success(self):
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(self.sli.id),
        )
        self.assertEquals(response.status_code, 302)
        response = self.client.get(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id})
        )
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_unauthorized_fail(self):
        # Test with anonymous user
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(0),
        )
        self.assertEquals(response.status_code, 403)

        # Test with non subscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(self.guy.id),
        )
        self.assertEquals(response.status_code, 403)

        # Check that the comment has never been created
        self.client.login(username="root", password="plop")
        response = self.client.get(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id})
        )
        self.assertNotContains(response, text="Superbe UV")

    def test_create_uv_comment_bad_form_fail(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id}),
            create_uv_comment_template(self.bibou.id, exclude_list=["grade_global"]),
        )

        self.assertEquals(response.status_code, 200)

        response = self.client.get(
            reverse("pedagogy:uv_detail", kwargs={"uv_id": self.uv.id})
        )
        self.assertNotContains(response, text="Superbe UV")


class UVCommentDeleteTest(TestCase):
    """
    Test UVComment deletion rights
    """

    def setUp(self):
        call_command("populate")
        comment_kwargs = create_uv_comment_template(
            User.objects.get(username="krophil").id
        )
        comment_kwargs["author"] = User.objects.get(id=comment_kwargs["author"])
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment = UVComment(**comment_kwargs)
        self.comment.save()

    def test_uv_comment_delete_root_success(self):
        self.client.login(username="root", password="plop")
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertFalse(UVComment.objects.filter(id=self.comment.id).exists())

    def test_uv_comment_delete_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertFalse(UVComment.objects.filter(id=self.comment.id).exists())

    def test_uv_comment_delete_author_success(self):
        self.client.login(username="krophil", password="plop")
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertFalse(UVComment.objects.filter(id=self.comment.id).exists())

    def test_uv_comment_delete_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertEquals(response.status_code, 403)

        # Unsbscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertEquals(response.status_code, 403)

        # Subscribed user (not author of the comment)
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        self.assertEquals(response.status_code, 403)

        # Check that the comment still exists
        self.assertTrue(UVComment.objects.filter(id=self.comment.id).exists())


class UVCommentUpdateTest(TestCase):
    """
    Test UVComment update rights
    """

    def setUp(self):
        call_command("populate")

        self.krophil = User.objects.get(username="krophil")

        # Prepare a comment
        comment_kwargs = create_uv_comment_template(self.krophil.id)
        comment_kwargs["author"] = self.krophil
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment = UVComment(**comment_kwargs)
        self.comment.save()

        # Prepare edit of this comment for post requests
        self.comment_edit = create_uv_comment_template(self.krophil.id)
        self.comment_edit["comment"] = "Edited"

    def test_uv_comment_update_root_success(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEquals(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEquals(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_author_success(self):
        self.client.login(username="krophil", password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEquals(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 403)

        # Unsbscribed user
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 403)

        # Subscribed user (not author of the comment)
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 403)

        # Check that the comment hasn't change
        self.comment.refresh_from_db()
        self.assertNotEquals(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_original_author_does_not_change(self):
        self.client.login(username="root", password="plop")
        self.comment_edit["author"] = User.objects.get(username="root").id

        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.comment.author, self.krophil)
