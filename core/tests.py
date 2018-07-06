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

import os

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User, Group, Page
from core.markdown import markdown

"""
to run these tests :
    python3 manage.py test
"""


class UserRegistrationTest(TestCase):
    def setUp(self):
        try:
            Group.objects.create(name="root")
        except Exception as e:
            print(e)

    def test_register_user_form_ok(self):
        """
        Should register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': 'Carlier',
                                                     'email': 'guy@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' in str(response.content))

    def test_register_user_form_fail_password(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop2',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_email(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou.git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_missing_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': '',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_missing_date_of_birth(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': '',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_missing_first_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': '',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_wrong_captcha(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Bibou',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'WRONG_CAPTCHA'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_register_user_form_fail_already_exists(self):
        """
        Should not register a user correctly
        """
        c = Client()
        c.post(reverse('core:register'), {'first_name': 'Guy',
                                          'last_name': 'Carlier',
                                          'email': 'bibou@git.an',
                                          'date_of_birth': '12/6/1942',
                                          'password1': 'plop',
                                          'password2': 'plop',
                                          'captcha_0': 'dummy-value',
                                          'captcha_1': 'PASSED'
                                          })
        response = c.post(reverse('core:register'), {'first_name': 'Bibou',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'date_of_birth': '12/6/1942',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                     'captcha_0': 'dummy-value',
                                                     'captcha_1': 'PASSED'
                                                     })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_FAIL' in str(response.content))

    def test_login_success(self):
        """
        Should login a user correctly
        """
        c = Client()
        c.post(reverse('core:register'), {'first_name': 'Guy',
                                          'last_name': 'Carlier',
                                          'email': 'bibou@git.an',
                                          'date_of_birth': '12/6/1942',
                                          'password1': 'plop',
                                          'password2': 'plop',
                                          'captcha_0': 'dummy-value',
                                          'captcha_1': 'PASSED'
                                          })
        response = c.post(reverse('core:login'), {'username': 'gcarlier', 'password': 'plop'})
        self.assertTrue(response.status_code == 302)
        #self.assertTrue('Hello, world' in str(response.content))

    def test_login_fail(self):
        """
        Should not login a user correctly
        """
        c = Client()
        c.post(reverse('core:register'), {'first_name': 'Guy',
                                          'last_name': 'Carlier',
                                          'email': 'bibou@git.an',
                                          'date_of_birth': '12/6/1942',
                                          'password1': 'plop',
                                          'password2': 'plop',
                                          'captcha_0': 'dummy-value',
                                          'captcha_1': 'PASSED'
                                          })
        response = c.post(reverse('core:login'), {'username': 'gcarlier', 'password': 'guy'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue("""<p>Votre nom d\\'utilisateur et votre mot de passe ne correspondent pas. Merci de r\\xc3\\xa9essayer.</p>""" in str(response.content))

class MarkdownTest(TestCase):
    def test_full_markdown_syntax(self):
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root_path) + '/doc/SYNTAX.md', 'r') as md_file:
            md = md_file.read()
        with open(os.path.join(root_path) + '/doc/SYNTAX.html', 'r') as html_file:
            html = html_file.read()
        result = markdown(md)
        self.assertTrue(result == html)

class PageHandlingTest(TestCase):
    def setUp(self):
        try:
            Group.objects.create(name="root")
            u = User(username='root', last_name="", first_name="Bibou",
                     email="ae.info@utbm.fr",
                     date_of_birth="1942-06-12",
                     is_superuser=True, is_staff=True)
            u.set_password("plop")
            u.save()
            self.client.login(username='root', password='plop')
        except Exception as e:
            print(e)

    def test_create_page_ok(self):
        """
        Should create a page correctly
        """
        self.client.post(reverse('core:page_new'), {
            'parent': '',
            'name': 'guy',
            'owner_group': 1,
        })
        response = self.client.get(reverse('core:page', kwargs={'page_name': 'guy'}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<a href="/page/guy/hist">' in str(response.content))

    def test_create_child_page_ok(self):
        """
        Should create a page correctly
        """
        self.client.post(reverse('core:page_new'), {
            'parent': '',
            'name': 'guy',
            'owner_group': '1',
        })
        response = self.client.post(reverse('core:page_new'), {
            'parent': '1',
            'name': 'bibou',
            'owner_group': '1',
        })
        response = self.client.get(reverse('core:page', kwargs={'page_name': 'guy/bibou'}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<a href="/page/guy/bibou/">' in str(response.content))

    def test_access_child_page_ok(self):
        """
        Should display a page correctly
        """
        parent = Page(name="guy", owner_group=Group.objects.filter(id=1).first())
        parent.save(force_lock=True)
        page = Page(name="bibou", owner_group=Group.objects.filter(id=1).first(), parent=parent)
        page.save(force_lock=True)
        response = self.client.get(reverse('core:page', kwargs={'page_name': 'guy/bibou'}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<a href="/page/guy/bibou/edit">\\xc3\\x89diter</a>' in str(response.content))

    def test_access_page_not_found(self):
        """
        Should not display a page correctly
        """
        response = self.client.get(reverse('core:page', kwargs={'page_name': 'swagg'}))
        response = self.client.get("/page/swagg/")
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<a href="/page/create?page=swagg">' in str(response.content))

    def test_create_page_markdown_safe(self):
        """
        Should format the markdown and escape html correctly
        """
        self.client.post(reverse('core:page_new'), {
            'parent': '',
            'name': 'guy',
            'owner_group': '1',
        })
        self.client.post(reverse('core:page_edit', kwargs={'page_name': 'guy'}), {
            'title': 'Bibou',
            'content':
            '''Guy *bibou*

http://git.an

# Swag

<guy>Bibou</guy>

<script>alert('Guy');</script>
''',
        })
        response = self.client.get(reverse('core:page', kwargs={'page_name': 'guy'}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue('<p>Guy <em>bibou</em></p>\\n<p><a href="http://git.an">http://git.an</a></p>\\n' +
                        '<h1>Swag</h1>\\n&lt;guy&gt;Bibou&lt;/guy&gt;' +
                        "&lt;script&gt;alert(\\'Guy\\');&lt;/script&gt;" in str(response.content))

# TODO: many tests on the pages:
#   - renaming a page
#   - changing a page's parent --> check that page's children's full_name
#   - changing the different groups of the page


class FileHandlingTest(TestCase):
    def setUp(self):
        try:
            call_command("populate")
            self.subscriber = User.objects.filter(username="subscriber").first()
            self.client.login(username='subscriber', password='plop')
        except Exception as e:
            print(e)

    def test_create_folder_home(self):
        response = self.client.post(reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}),
                                    {"folder_name": "GUY_folder_test"})
        self.assertTrue(response.status_code == 302)
        response = self.client.get(reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("GUY_folder_test</a>" in str(response.content))

    def test_upload_file_home(self):
        with open("/bin/ls", "rb") as f:
            response = self.client.post(reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}),
                                        {"file_field": f})
        self.assertTrue(response.status_code == 302)
        response = self.client.get(reverse("core:file_detail", kwargs={"file_id": self.subscriber.home.id}))
        self.assertTrue(response.status_code == 200)
        self.assertTrue("ls</a>" in str(response.content))
