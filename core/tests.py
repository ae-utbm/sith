from django.test import SimpleTestCase, Client
from django.core.urlresolvers import reverse

from .models import User
from .forms import RegisteringForm, LoginForm

class UserRegistrationTest(SimpleTestCase):
    def test_register_user_form_ok(self):
        """
        Should register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': 'Carlier',
                                                     'email': 'guy@git.an',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
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
                                                     'password1': 'plop',
                                                     'password2': 'plop2',
                                                    })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' not in str(response.content))

    def test_register_user_form_fail_email(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou.git.an',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                    })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' not in str(response.content))

    def test_register_user_form_fail_missing_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': 'Guy',
                                                     'last_name': '',
                                                     'email': 'bibou@git.an',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                    })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' not in str(response.content))

    def test_register_user_form_fail_missing_first_name(self):
        """
        Should not register a user correctly
        """
        c = Client()
        response = c.post(reverse('core:register'), {'first_name': '',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                    })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' not in str(response.content))

    def test_register_user_form_fail_already_exists(self):
        """
        Should not register a user correctly
        """
        c = Client()
        c.post(reverse('core:register'), {'first_name': 'Guy',
                                          'last_name': 'Carlier',
                                          'email': 'bibou@git.an',
                                          'password1': 'plop',
                                          'password2': 'plop',
                                         })
        response = c.post(reverse('core:register'), {'first_name': 'Bibou',
                                                     'last_name': 'Carlier',
                                                     'email': 'bibou@git.an',
                                                     'password1': 'plop',
                                                     'password2': 'plop',
                                                    })
        self.assertTrue(response.status_code == 200)
        self.assertTrue('TEST_REGISTER_USER_FORM_OK' not in str(response.content))

