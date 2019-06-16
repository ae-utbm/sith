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

from pedagogy.models import UV


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

    @staticmethod
    def create_uv_template(user_id, code="IFC1", exclude_list=[]):
        """
        Factory to help UV creation in post requests
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

    def test_create_uv_admin_success(self):
        self.client.login(username="root", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(self.bibou.id)
        )
        self.assertEquals(response.status_code, 302)
        self.assertTrue(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_pedagogy_admin_success(self):
        self.client.login(username="tutu", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(self.tutu.id)
        )
        self.assertEquals(response.status_code, 302)
        self.assertTrue(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_unauthorized_fail(self):
        # Test with anonymous user
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(0)
        )
        self.assertEquals(response.status_code, 403)

        # Test with subscribed user
        self.client.login(username="sli", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(self.sli.id)
        )
        self.assertEquals(response.status_code, 403)

        # Test with non subscribed user
        self.client.login(username="guy", password="plop")
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(self.guy.id)
        )
        self.assertEquals(response.status_code, 403)

        # Check that the UV has never been created
        self.assertFalse(UV.objects.filter(code="IFC1").exists())

    def test_create_uv_bad_request_fail(self):
        self.client.login(username="tutu", password="plop")

        # Test with wrong user id (if someone cheats on the hidden input)
        response = self.client.post(
            reverse("pedagogy:uv_create"), self.create_uv_template(self.bibou.id)
        )
        self.assertNotEquals(response.status_code, 302)
        self.assertEquals(response.status_code, 200)

        # Remove a required field
        response = self.client.post(
            reverse("pedagogy:uv_create"),
            self.create_uv_template(self.tutu.id, exclude_list=["title"]),
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

    def uv_list_display_success(self):
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

    def uv_list_display_fail(self):
        # Don't display for anonymous user
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertEquals(response.status_code, 403)

        # Don't display for none subscribed users
        self.client.login(username="guy", password="plop")
        response = self.client.get(reverse("pedagogy:guide"))
        self.assertEquals(response.status_code, 403)
