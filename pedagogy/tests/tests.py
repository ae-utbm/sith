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
from urllib.parse import quote

import pytest
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pytest_django.asserts import assertRedirects

from core.baker_recipes import old_subscriber_user, subscriber_user
from core.models import Notification, User
from pedagogy.models import UV, UVComment, UVCommentReport


def create_uv_template(user_id, code="IFC1", exclude_list=None):
    """Factory to help UV creation/update in post requests."""
    if exclude_list is None:
        exclude_list = []
    uv = {
        "code": code,
        "author": user_id,
        "credit_type": "TM",
        "semester": "SPRING",
        "language": "FR",
        "department": "TC",
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


class TestUVCreation(TestCase):
    """Test uv creation."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.create_uv_url = reverse("pedagogy:uv_create")

    def test_create_uv_admin_success(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            self.create_uv_url, create_uv_template(self.bibou.id)
        )
        assert response.status_code == 302
        assert UV.objects.filter(code="IFC1").exists()

    def test_create_uv_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        response = self.client.post(
            self.create_uv_url, create_uv_template(self.tutu.id)
        )
        assert response.status_code == 302
        assert UV.objects.filter(code="IFC1").exists()

    def test_create_uv_unauthorized_fail(self):
        # Test with anonymous user
        response = self.client.post(self.create_uv_url, create_uv_template(0))
        assertRedirects(
            response, reverse("core:login") + f"?next={quote(self.create_uv_url)}"
        )

        # Test with subscribed user
        self.client.force_login(self.sli)
        response = self.client.post(self.create_uv_url, create_uv_template(self.sli.id))
        assert response.status_code == 403

        # Test with non subscribed user
        self.client.force_login(self.guy)
        response = self.client.post(self.create_uv_url, create_uv_template(self.guy.id))
        assert response.status_code == 403

        # Check that the UV has never been created
        assert not UV.objects.filter(code="IFC1").exists()

    def test_create_uv_bad_request_fail(self):
        self.client.force_login(self.tutu)

        # Test with wrong user id (if someone cheats on the hidden input)
        response = self.client.post(
            self.create_uv_url, create_uv_template(self.bibou.id)
        )
        assert response.status_code == 200

        # Remove a required field
        response = self.client.post(
            self.create_uv_url,
            create_uv_template(self.tutu.id, exclude_list=["title"]),
        )
        assert response.status_code == 200

        # Check that the UV hase never been created
        assert not UV.objects.filter(code="IFC1").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("username", "expected_code"),
    [
        ("root", 200),
        ("tutu", 200),
        ("sli", 200),
        ("old_subscriber", 200),
        ("public", 403),
    ],
)
def test_guide_permissions(client: Client, username: str, expected_code: int):
    client.force_login(User.objects.get(username=username))
    res = client.get(reverse("pedagogy:guide"))
    assert res.status_code == expected_code


@pytest.mark.django_db
def test_guide_anonymous_permission_denied(client: Client):
    res = client.get(reverse("pedagogy:guide"))
    assert res.status_code == 302


class TestUVDelete(TestCase):
    """Test UV deletion rights."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.uv = UV.objects.get(code="PA00")
        cls.delete_uv_url = reverse("pedagogy:uv_delete", kwargs={"uv_id": cls.uv.id})

    def test_uv_delete_root_success(self):
        self.client.force_login(self.bibou)
        self.client.post(self.delete_uv_url)
        assert not UV.objects.filter(pk=self.uv.pk).exists()

    def test_uv_delete_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        self.client.post(self.delete_uv_url)
        assert not UV.objects.filter(pk=self.uv.pk).exists()

    def test_uv_delete_pedagogy_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(self.delete_uv_url)
        assertRedirects(response, reverse("core:login") + f"?next={self.delete_uv_url}")
        assert UV.objects.filter(pk=self.uv.pk).exists()

        # Not subscribed user
        self.client.force_login(self.guy)
        response = self.client.post(self.delete_uv_url)
        assert response.status_code == 403
        assert UV.objects.filter(pk=self.uv.pk).exists()

        # Simply subscribed user
        self.client.force_login(self.sli)
        response = self.client.post(self.delete_uv_url)
        assert response.status_code == 403
        assert UV.objects.filter(pk=self.uv.pk).exists()


class TestUVUpdate(TestCase):
    """Test UV update rights."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.uv = UV.objects.get(code="PA00")
        cls.update_uv_url = reverse("pedagogy:uv_update", kwargs={"uv_id": cls.uv.id})

    def test_uv_update_root_success(self):
        self.client.force_login(self.bibou)
        self.client.post(
            self.update_uv_url, create_uv_template(self.bibou.id, code="PA00")
        )
        self.uv.refresh_from_db()
        assert self.uv.credit_type == "TM"

    def test_uv_update_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        self.client.post(
            self.update_uv_url, create_uv_template(self.bibou.id, code="PA00")
        )
        self.uv.refresh_from_db()
        assert self.uv.credit_type == "TM"

    def test_uv_update_original_author_does_not_change(self):
        self.client.force_login(self.tutu)
        response = self.client.post(
            self.update_uv_url,
            create_uv_template(self.tutu.id, code="PA00"),
        )
        assert response.status_code == 200
        self.uv.refresh_from_db()
        assert self.uv.author == self.bibou

    def test_uv_update_pedagogy_unauthorized_fail(self):
        # Anonymous user
        response = self.client.post(
            self.update_uv_url, create_uv_template(self.bibou.id, code="PA00")
        )
        assertRedirects(
            response, reverse("core:login") + f"?next={quote(self.update_uv_url)}"
        )

        # Not subscribed user
        self.client.force_login(self.guy)
        response = self.client.post(
            self.update_uv_url, create_uv_template(self.bibou.id, code="PA00")
        )
        assert response.status_code == 403

        # Simply subscribed user
        self.client.force_login(self.sli)
        response = self.client.post(
            self.update_uv_url, create_uv_template(self.bibou.id, code="PA00")
        )
        assert response.status_code == 403

        # Check that the UV has not changed
        self.uv.refresh_from_db()
        assert self.uv.credit_type == "OM"


# UVComment class tests


def create_uv_comment_template(user_id, uv_code="PA00", exclude_list=None):
    """Factory to help UVComment creation/update in post requests."""
    if exclude_list is None:
        exclude_list = []
    comment = {
        "author": user_id,
        "uv": UV.objects.get(code=uv_code).id,
        "grade_global": 4,
        "grade_utility": 4,
        "grade_interest": 4,
        "grade_teaching": -1,
        "grade_work_load": 2,
        "comment": "Superbe UV qui fait vivre la vie associative de l'école",
    }
    for excluded in exclude_list:
        comment.pop(excluded)
    return comment


class TestUVCommentCreationAndDisplay(TestCase):
    """Test UVComment creation and its display.

    Display and creation are the same view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.uv = UV.objects.get(code="PA00")
        cls.uv_url = reverse("pedagogy:uv_detail", kwargs={"uv_id": cls.uv.id})

    def test_create_uv_comment_admin_success(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            self.uv_url, create_uv_comment_template(self.bibou.id)
        )
        self.assertRedirects(response, self.uv_url)
        response = self.client.get(self.uv_url)
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        response = self.client.post(
            self.uv_url, create_uv_comment_template(self.tutu.id)
        )
        self.assertRedirects(response, self.uv_url)
        response = self.client.get(self.uv_url)
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_unauthorized_fail(self):
        nb_comments = self.uv.comments.count()
        # Test with anonymous user
        response = self.client.post(self.uv_url, create_uv_comment_template(0))
        assertRedirects(response, reverse("core:login") + f"?next={quote(self.uv_url)}")

        # Test with non subscribed user
        self.client.force_login(self.guy)
        response = self.client.post(
            self.uv_url, create_uv_comment_template(self.guy.id)
        )
        assert response.status_code == 403

        # Check that no comment has been created
        assert self.uv.comments.count() == nb_comments

    def test_create_uv_comment_bad_form_fail(self):
        nb_comments = self.uv.comments.count()
        self.client.force_login(self.bibou)
        response = self.client.post(
            self.uv_url,
            create_uv_comment_template(self.bibou.id, exclude_list=["grade_global"]),
        )

        assert response.status_code == 200
        assert self.uv.comments.count() == nb_comments

    def test_create_uv_comment_twice_fail(self):
        # Checks that the has_user_already_commented method works proprely
        assert not self.uv.has_user_already_commented(self.bibou)

        # Create a first comment
        self.client.force_login(self.bibou)
        self.client.post(self.uv_url, create_uv_comment_template(self.bibou.id))

        # Checks that the has_user_already_commented method works proprely
        assert self.uv.has_user_already_commented(self.bibou)

        # Create the second comment
        comment = create_uv_comment_template(self.bibou.id)
        comment["comment"] = "Twice"
        response = self.client.post(self.uv_url, comment)
        assert response.status_code == 200
        assert UVComment.objects.filter(comment__contains="Superbe UV").exists()
        assert not UVComment.objects.filter(comment__contains="Twice").exists()
        self.assertContains(
            response,
            _(
                "You already posted a comment on this UV. "
                "If you want to comment again, "
                "please modify or delete your previous comment."
            ),
        )

        # Ensure that there is no crash when no uv or no author is given
        self.client.post(
            self.uv_url, create_uv_comment_template(self.bibou.id, exclude_list=["uv"])
        )
        assert response.status_code == 200
        self.client.post(
            self.uv_url,
            create_uv_comment_template(self.bibou.id, exclude_list=["author"]),
        )
        assert response.status_code == 200


class TestUVCommentDelete(TestCase):
    """Test UVComment deletion rights."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.krophil = User.objects.get(username="krophil")

    def setUp(self):
        comment_kwargs = create_uv_comment_template(
            User.objects.get(username="krophil").id
        )
        comment_kwargs["author"] = User.objects.get(id=comment_kwargs["author"])
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment = UVComment(**comment_kwargs)
        self.comment.save()

    def test_uv_comment_delete_root_success(self):
        self.client.force_login(self.bibou)
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert not UVComment.objects.filter(id=self.comment.id).exists()

    def test_uv_comment_delete_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert not UVComment.objects.filter(id=self.comment.id).exists()

    def test_uv_comment_delete_author_success(self):
        self.client.force_login(self.krophil)
        self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert not UVComment.objects.filter(id=self.comment.id).exists()

    def test_uv_comment_delete_unauthorized_fail(self):
        delete_url = reverse(
            "pedagogy:comment_delete", kwargs={"comment_id": self.comment.id}
        )
        # Anonymous user
        response = self.client.post(delete_url)
        assertRedirects(response, reverse("core:login") + f"?next={quote(delete_url)}")

        # Unsbscribed user
        self.client.force_login(self.guy)
        response = self.client.post(delete_url)
        assert response.status_code == 403

        # Subscribed user (not author of the comment)
        self.client.force_login(self.sli)
        response = self.client.post(delete_url)
        assert response.status_code == 403

        # Check that the comment still exists
        assert UVComment.objects.filter(id=self.comment.id).exists()


class TestUVCommentUpdate(TestCase):
    """Test UVComment update rights."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.krophil = User.objects.get(username="krophil")

    def setUp(self):
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
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 302
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_pedagogy_admin_success(self):
        self.client.force_login(self.tutu)
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 302
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_author_success(self):
        self.client.force_login(self.krophil)
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 302
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_unauthorized_fail(self):
        update_url = reverse(
            "pedagogy:comment_update", kwargs={"comment_id": self.comment.id}
        )
        # Anonymous user
        response = self.client.post(update_url, self.comment_edit)
        assertRedirects(response, reverse("core:login") + f"?next={quote(update_url)}")

        # Unsbscribed user
        self.client.force_login(old_subscriber_user.make())
        response = self.client.post(update_url, self.comment_edit)
        assert response.status_code == 403

        # Subscribed user (not author of the comment)
        self.client.force_login(subscriber_user.make())
        response = self.client.post(update_url, self.comment_edit)
        assert response.status_code == 403

        # Check that the comment hasn't change
        self.comment.refresh_from_db()
        self.assertNotEqual(self.comment.comment, self.comment_edit["comment"])

    def test_uv_comment_update_original_author_does_not_change(self):
        self.client.force_login(self.bibou)
        self.comment_edit["author"] = User.objects.get(username="root").id

        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 200
        self.assertEqual(self.comment.author, self.krophil)


class TestUVModerationForm(TestCase):
    """Assert access rights and if the form works well."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")
        cls.krophil = User.objects.get(username="krophil")

    def setUp(self):
        # Prepare a comment
        comment_kwargs = create_uv_comment_template(self.krophil.id)
        comment_kwargs["author"] = self.krophil
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment_1 = UVComment(**comment_kwargs)
        self.comment_1.save()

        # Prepare another comment
        comment_kwargs = create_uv_comment_template(self.krophil.id)
        comment_kwargs["author"] = self.krophil
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment_2 = UVComment(**comment_kwargs)
        self.comment_2.save()

        # Prepare a comment report for comment 1
        self.report_1 = UVCommentReport(
            comment=self.comment_1, reporter=self.krophil, reason="C'est moche"
        )
        self.report_1.save()
        self.report_1_bis = UVCommentReport(
            comment=self.comment_1, reporter=self.krophil, reason="C'est moche 2"
        )
        self.report_1_bis.save()

        # Prepare a comment report for comment 2
        self.report_2 = UVCommentReport(
            comment=self.comment_2, reporter=self.krophil, reason="C'est moche"
        )
        self.report_2.save()

    def test_access_authorized_success(self):
        # Test with root
        self.client.force_login(self.bibou)
        response = self.client.get(reverse("pedagogy:moderation"))
        assert response.status_code == 200

        # Test with pedagogy admin
        self.client.force_login(self.tutu)
        response = self.client.get(reverse("pedagogy:moderation"))
        assert response.status_code == 200

    def test_access_unauthorized_fail(self):
        moderation_url = reverse("pedagogy:moderation")
        # Test with anonymous user
        response = self.client.get(moderation_url)
        assertRedirects(
            response, reverse("core:login") + f"?next={quote(moderation_url)}"
        )

        # Test with unsubscribed user
        self.client.force_login(self.guy)
        response = self.client.get(moderation_url)
        assert response.status_code == 403

        # Test with subscribed user
        self.client.force_login(self.sli)
        response = self.client.get(moderation_url)
        assert response.status_code == 403

    def test_do_nothing(self):
        self.client.force_login(self.bibou)
        response = self.client.post(reverse("pedagogy:moderation"))
        assert response.status_code == 302

        # Test that nothing has changed
        assert UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert UVComment.objects.filter(id=self.comment_1.id).exists()
        assert UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()
        assert UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert UVComment.objects.filter(id=self.comment_2.id).exists()

    def test_delete_comment(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"), {"accepted_reports": [self.report_1.id]}
        )
        assert response.status_code == 302

        # Test that the comment and it's associated report has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert not UVComment.objects.filter(id=self.comment_1.id).exists()
        # Test that the bis report has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()

        # Test that the other comment and report still exists
        assert UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert UVComment.objects.filter(id=self.comment_2.id).exists()

    def test_delete_comment_bulk(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"),
            {"accepted_reports": [self.report_1.id, self.report_2.id]},
        )
        assert response.status_code == 302

        # Test that comments and their associated reports has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert not UVComment.objects.filter(id=self.comment_1.id).exists()
        assert not UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert not UVComment.objects.filter(id=self.comment_2.id).exists()
        # Test that the bis report has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()

    def test_delete_comment_with_bis(self):
        # Test case if two reports targets the same comment and are both deleted
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"),
            {"accepted_reports": [self.report_1.id, self.report_1_bis.id]},
        )
        assert response.status_code == 302

        # Test that the comment and it's associated report has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert not UVComment.objects.filter(id=self.comment_1.id).exists()
        # Test that the bis report has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()

    def test_delete_report(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"), {"denied_reports": [self.report_1.id]}
        )
        assert response.status_code == 302

        # Test that the report has been deleted and that the comment still exists
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert UVComment.objects.filter(id=self.comment_1.id).exists()
        # Test that the bis report is still there
        assert UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()

        # Test that the other comment and report still exists
        assert UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert UVComment.objects.filter(id=self.comment_2.id).exists()

    def test_delete_report_bulk(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"),
            {
                "denied_reports": [
                    self.report_1.id,
                    self.report_1_bis.id,
                    self.report_2.id,
                ]
            },
        )
        assert response.status_code == 302

        # Test that every reports has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert not UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()
        assert not UVCommentReport.objects.filter(id=self.report_2.id).exists()
        # Test that comments still exists
        assert UVComment.objects.filter(id=self.comment_1.id).exists()
        assert UVComment.objects.filter(id=self.comment_2.id).exists()

    def test_delete_mixed(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"),
            {
                "accepted_reports": [self.report_2.id],
                "denied_reports": [self.report_1.id],
            },
        )
        assert response.status_code == 302

        # Test that report 2 and his comment has been deleted
        assert not UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert not UVComment.objects.filter(id=self.comment_2.id).exists()

        # Test that report 1 has been deleted and it's comment still exists
        assert not UVCommentReport.objects.filter(id=self.report_1.id).exists()
        assert UVComment.objects.filter(id=self.comment_1.id).exists()

        # Test that report 1 bis is still there
        assert UVCommentReport.objects.filter(id=self.report_1_bis.id).exists()

    def test_delete_mixed_with_bis(self):
        self.client.force_login(self.bibou)
        response = self.client.post(
            reverse("pedagogy:moderation"),
            {
                "accepted_reports": [self.report_1.id],
                "denied_reports": [self.report_1_bis.id],
            },
        )
        assert response.status_code == 302

        # Test that report 1 and 1 bis has been deleted
        assert not UVCommentReport.objects.filter(
            id__in=[self.report_1.id, self.report_1_bis.id]
        ).exists()

        # Test that comment 1 has been deleted
        assert not UVComment.objects.filter(id=self.comment_1.id).exists()

        # Test that report and comment 2 still exists
        assert UVCommentReport.objects.filter(id=self.report_2.id).exists()
        assert UVComment.objects.filter(id=self.comment_2.id).exists()


class TestUVCommentReportCreate(TestCase):
    """Test report creation view.

    Assert access rights and if you can create with it.
    """

    def setUp(self):
        self.krophil = User.objects.get(username="krophil")
        self.tutu = User.objects.get(username="tutu")

        # Prepare a comment
        comment_kwargs = create_uv_comment_template(self.krophil.id)
        comment_kwargs["author"] = self.krophil
        comment_kwargs["uv"] = UV.objects.get(id=comment_kwargs["uv"])
        self.comment = UVComment(**comment_kwargs)
        self.comment.save()

    def create_report_test(self, username: str, *, success: bool):
        self.client.login(username=username, password="plop")
        response = self.client.post(
            reverse("pedagogy:comment_report", kwargs={"comment_id": self.comment.id}),
            {
                "comment": self.comment.id,
                "reporter": User.objects.get(username=username).id,
                "reason": "C'est moche",
            },
        )
        if success:
            assert response.status_code == 302
        else:
            assert response.status_code == 403
        self.assertEqual(UVCommentReport.objects.all().exists(), success)

    def test_create_report_root_success(self):
        self.create_report_test("root", success=True)

    def test_create_report_pedagogy_admin_success(self):
        self.create_report_test("tutu", success=True)

    def test_create_report_subscriber_success(self):
        self.create_report_test("sli", success=True)

    def test_create_report_unsubscribed_fail(self):
        self.create_report_test("guy", success=False)

    def test_create_report_anonymous_fail(self):
        report_url = reverse(
            "pedagogy:comment_report", kwargs={"comment_id": self.comment.id}
        )
        response = self.client.post(
            report_url,
            {"comment": self.comment.id, "reporter": 0, "reason": "C'est moche"},
        )
        assertRedirects(response, reverse("core:login") + f"?next={quote(report_url)}")
        assert not UVCommentReport.objects.all().exists()

    def test_notifications(self):
        assert not self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").exists()
        # Create a comment report
        self.create_report_test("tutu", success=True)

        # Check that a notification has been created for pedagogy admins
        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").exists()

        # Check that only pedagogy admins recieves this notification
        for notif in Notification.objects.filter(type="PEDAGOGY_MODERATION").all():
            assert notif.user.is_in_group(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)

        # Check that notifications are not duplicated if not viewed
        self.create_report_test("tutu", success=True)
        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").count() == 1

        # Check that a new notification is created when the old one has been viewed
        notif = self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").first()
        notif.viewed = True
        notif.save()

        self.create_report_test("tutu", success=True)

        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").count() == 2
