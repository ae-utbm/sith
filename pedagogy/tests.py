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

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import Notification, User
from pedagogy.models import UV, UVComment, UVCommentReport


def create_uv_template(user_id, code="IFC1", exclude_list=None):
    """
    Factory to help UV creation/update in post requests
    """
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


class UVCreation(TestCase):
    """
    Test uv creation
    """

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
        assert response.status_code == 403

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


class UVListTest(TestCase):
    """Test guide display rights."""

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")

    def test_uv_list_display_success(self):
        # Display for root
        self.client.force_login(self.bibou)
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

        # Display for pedagogy admin
        self.client.force_login(self.tutu)
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

        # Display for simple subscriber
        self.client.force_login(self.sli)
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertContains(response, text="PA00")

    def test_uv_list_display_fail(self):
        # Don't display for anonymous user
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 403

        # Don't display for none subscribed users
        self.client.force_login(self.guy)
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 403


class UVDeleteTest(TestCase):
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
        assert response.status_code == 403
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


class UVUpdateTest(TestCase):
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
        assert response.status_code == 403

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
    """
    Factory to help UVComment creation/update in post requests
    """
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


class UVCommentCreationAndDisplay(TestCase):
    """
    Test UVComment creation and it's display
    Display and creation are the same view
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

    def test_create_uv_comment_subscriber_success(self):
        self.client.force_login(self.sli)
        response = self.client.post(
            self.uv_url, create_uv_comment_template(self.sli.id)
        )
        self.assertRedirects(response, self.uv_url)
        response = self.client.get(self.uv_url)
        self.assertContains(response, text="Superbe UV")

    def test_create_uv_comment_unauthorized_fail(self):
        nb_comments = self.uv.comments.count()
        # Test with anonymous user
        response = self.client.post(self.uv_url, create_uv_comment_template(0))
        assert response.status_code == 403

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
                "You already posted a comment on this UV. If you want to comment again, please modify or delete your previous comment."
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


class UVCommentDeleteTest(TestCase):
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
        # Anonymous user
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert response.status_code == 403

        # Unsbscribed user
        self.client.force_login(self.guy)
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert response.status_code == 403

        # Subscribed user (not author of the comment)
        self.client.force_login(self.sli)
        response = self.client.post(
            reverse("pedagogy:comment_delete", kwargs={"comment_id": self.comment.id})
        )
        assert response.status_code == 403

        # Check that the comment still exists
        assert UVComment.objects.filter(id=self.comment.id).exists()


class UVCommentUpdateTest(TestCase):
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
        # Anonymous user
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 403

        # Unsbscribed user
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
        assert response.status_code == 403

        # Subscribed user (not author of the comment)
        response = self.client.post(
            reverse("pedagogy:comment_update", kwargs={"comment_id": self.comment.id}),
            self.comment_edit,
        )
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


class UVSearchTest(TestCase):
    """
    Test UV guide rights for view and API
    Test that the API is working well
    """

    @classmethod
    def setUpTestData(cls):
        cls.bibou = User.objects.get(username="root")
        cls.tutu = User.objects.get(username="tutu")
        cls.sli = User.objects.get(username="sli")
        cls.guy = User.objects.get(username="guy")

    def setUp(self):
        call_command("update_index", "pedagogy")

    def test_get_page_authorized_success(self):
        # Test with root user
        self.client.force_login(self.bibou)
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 200

        # Test with pedagogy admin
        self.client.force_login(self.tutu)
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 200

        # Test with subscribed user
        self.client.force_login(self.sli)
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 200

    def test_get_page_unauthorized_fail(self):
        # Test with anonymous user
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 403

        # Test with not subscribed user
        self.client.force_login(self.guy)
        response = self.client.get(reverse("pedagogy:guide"))
        assert response.status_code == 403

    def test_search_pa00_success(self):
        self.client.force_login(self.sli)

        # Search with UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "PA00"})
        self.assertContains(response, text="PA00")

        # Search with first letter of UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "P"})
        self.assertContains(response, text="PA00")

        # Search with first letter of UV code in lowercase
        response = self.client.get(reverse("pedagogy:guide"), {"search": "p"})
        self.assertContains(response, text="PA00")

        # Search with UV title
        response = self.client.get(
            reverse("pedagogy:guide"), {"search": "participation"}
        )
        self.assertContains(response, text="PA00")

        # Search with UV manager
        response = self.client.get(reverse("pedagogy:guide"), {"search": "HEYBERGER"})
        self.assertContains(response, text="PA00")

        # Search with department
        response = self.client.get(reverse("pedagogy:guide"), {"department": "HUMA"})
        self.assertContains(response, text="PA00")

        # Search with semester
        response = self.client.get(reverse("pedagogy:guide"), {"semester": "AUTUMN"})
        self.assertContains(response, text="PA00")

        response = self.client.get(reverse("pedagogy:guide"), {"semester": "SPRING"})
        self.assertContains(response, text="PA00")

        response = self.client.get(
            reverse("pedagogy:guide"), {"semester": "AUTUMN_AND_SPRING"}
        )
        self.assertContains(response, text="PA00")

        # Search with language
        response = self.client.get(reverse("pedagogy:guide"), {"language": "FR"})
        self.assertContains(response, text="PA00")

        # Search with credit type
        response = self.client.get(reverse("pedagogy:guide"), {"credit_type": "OM"})
        self.assertContains(response, text="PA00")

        # Search with combinaison of all
        response = self.client.get(
            reverse("pedagogy:guide"),
            {
                "search": "P",
                "department": "HUMA",
                "semester": "AUTUMN",
                "language": "FR",
                "credit_type": "OM",
            },
        )
        self.assertContains(response, text="PA00")

        # Test json briefly
        response = self.client.get(
            reverse("pedagogy:guide"),
            {
                "json": "t",
                "search": "P",
                "department": "HUMA",
                "semester": "AUTUMN",
                "language": "FR",
                "credit_type": "OM",
            },
        )
        self.assertJSONEqual(
            response.content,
            [
                {
                    "id": 1,
                    "absolute_url": "/pedagogy/uv/1/",
                    "update_url": "/pedagogy/uv/1/edit/",
                    "delete_url": "/pedagogy/uv/1/delete/",
                    "code": "PA00",
                    "author": 0,
                    "credit_type": "OM",
                    "semester": "AUTUMN_AND_SPRING",
                    "language": "FR",
                    "credits": 5,
                    "department": "HUMA",
                    "title": "Participation dans une association \u00e9tudiante",
                    "manager": "Laurent HEYBERGER",
                    "objectives": "* Permettre aux \u00e9tudiants de r\u00e9aliser, pendant un semestre, un projet culturel ou associatif et de le valoriser.",
                    "program": "* Semestre pr\u00e9c\u00e9dent proposition d'un projet et d'un cahier des charges\n* Evaluation par un jury de six membres\n* Si accord r\u00e9alisation dans le cadre de l'UV\n* Compte-rendu de l'exp\u00e9rience\n* Pr\u00e9sentation",
                    "skills": "* G\u00e9rer un projet associatif ou une action \u00e9ducative en autonomie:\n* en produisant un cahier des charges qui -d\u00e9finit clairement le contexte du projet personnel -pose les jalons de ce projet -estime de mani\u00e8re r\u00e9aliste les moyens et objectifs du projet -d\u00e9finit exactement les livrables attendus\n    * en \u00e9tant capable de respecter ce cahier des charges ou, le cas \u00e9ch\u00e9ant, de r\u00e9viser le cahier des charges de mani\u00e8re argument\u00e9e.\n* Relater son exp\u00e9rience dans un rapport:\n* qui permettra \u00e0 d'autres \u00e9tudiants de poursuivre les actions engag\u00e9es\n* qui montre la capacit\u00e9 \u00e0 s'auto-\u00e9valuer et \u00e0 adopter une distance critique sur son action.",
                    "key_concepts": "* Autonomie\n* Responsabilit\u00e9\n* Cahier des charges\n* Gestion de projet",
                    "hours_CM": 0,
                    "hours_TD": 0,
                    "hours_TP": 0,
                    "hours_THE": 121,
                    "hours_TE": 4,
                }
            ],
        )

    def test_search_pa00_fail(self):
        # Search with UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "IFC"})
        self.assertNotContains(response, text="PA00")

        # Search with first letter of UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "I"})
        self.assertNotContains(response, text="PA00")

        # Search with UV manager
        response = self.client.get(reverse("pedagogy:guide"), {"search": "GILLES"})
        self.assertNotContains(response, text="PA00")

        # Search with department
        response = self.client.get(reverse("pedagogy:guide"), {"department": "TC"})
        self.assertNotContains(response, text="PA00")

        # Search with semester
        response = self.client.get(reverse("pedagogy:guide"), {"semester": "CLOSED"})
        self.assertNotContains(response, text="PA00")

        # Search with language
        response = self.client.get(reverse("pedagogy:guide"), {"language": "EN"})
        self.assertNotContains(response, text="PA00")

        # Search with credit type
        response = self.client.get(reverse("pedagogy:guide"), {"credit_type": "TM"})
        self.assertNotContains(response, text="PA00")


class UVModerationFormTest(TestCase):
    """
    Test moderation view
    Assert access rights and if the form works well
    """

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
        # Test with anonymous user
        response = self.client.get(reverse("pedagogy:moderation"))
        assert response.status_code == 403

        # Test with unsubscribed user
        self.client.force_login(self.guy)
        response = self.client.get(reverse("pedagogy:moderation"))
        assert response.status_code == 403

        # Test with subscribed user
        self.client.force_login(self.sli)
        response = self.client.get(reverse("pedagogy:moderation"))
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


class UVCommentReportCreateTest(TestCase):
    """
    Test report creation view view
    Assert access rights and if you can create with it
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

    def create_report_test(self, username, success):
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
        self.create_report_test("root", True)

    def test_create_report_pedagogy_admin_success(self):
        self.create_report_test("tutu", True)

    def test_create_report_subscriber_success(self):
        self.create_report_test("sli", True)

    def test_create_report_unsubscribed_fail(self):
        self.create_report_test("guy", False)

    def test_create_report_anonymous_fail(self):
        response = self.client.post(
            reverse("pedagogy:comment_report", kwargs={"comment_id": self.comment.id}),
            {"comment": self.comment.id, "reporter": 0, "reason": "C'est moche"},
        )
        assert response.status_code == 403
        assert not UVCommentReport.objects.all().exists()

    def test_notifications(self):
        assert not self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").exists()
        # Create a comment report
        self.create_report_test("tutu", True)

        # Check that a notification has been created for pedagogy admins
        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").exists()

        # Check that only pedagogy admins recieves this notification
        for notif in Notification.objects.filter(type="PEDAGOGY_MODERATION").all():
            assert notif.user.is_in_group(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)

        # Check that notifications are not duplicated if not viewed
        self.create_report_test("tutu", True)
        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").count() == 1

        # Check that a new notification is created when the old one has been viewed
        notif = self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").first()
        notif.viewed = True
        notif.save()

        self.create_report_test("tutu", True)

        assert self.tutu.notifications.filter(type="PEDAGOGY_MODERATION").count() == 2
