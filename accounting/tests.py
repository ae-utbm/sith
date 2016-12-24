from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.conf import settings

from core.models import User
from counter.models import Counter
from accounting.models import GeneralJournal, Operation, AccountingType, SimplifiedAccountingType


class RefoundAccountTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        # reffil skia's account
        self.skia.customer.amount = 800
        self.skia.customer.save()

    def test_permission_denied(self):
        self.client.login(username='guy', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertTrue(response_get.status_code == 403)
        self.assertTrue(response_post.status_code == 403)

    def test_root_granteed(self):
        self.client.login(username='root', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        self.skia = User.objects.filter(username='skia').first()
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertFalse(response_get.status_code == 403)
        self.assertTrue('<form action="" method="post">' in str(response_get.content))
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue(self.skia.customer.amount == 0)

    def test_comptable_granteed(self):
        self.client.login(username='comptable', password='plop')
        response_post = self.client.post(reverse("accounting:refound_account"),
                                         {"user": self.skia.id})
        self.skia = User.objects.filter(username='skia').first()
        response_get = self.client.get(reverse("accounting:refound_account"))
        self.assertFalse(response_get.status_code == 403)
        self.assertTrue('<form action="" method="post">' in str(response_get.content))
        self.assertFalse(response_post.status_code == 403)
        self.assertTrue(self.skia.customer.amount == 0)

class JournalTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.journal = GeneralJournal.objects.filter(id = 1).first()

    def test_permission_granted(self):
        self.client.login(username='comptable', password='plop')
        response_get = self.client.get(reverse("accounting:journal_details", args=[self.journal.id]))

        self.assertTrue(response_get.status_code == 200)
        self.assertTrue('<td>M\\xc3\\xa9thode de paiement</td>' in str(response_get.content))

    def test_permission_not_granted(self):
        self.client.login(username='skia', password='plop')
        response_get = self.client.get(reverse("accounting:journal_details", args=[self.journal.id]))

        self.assertTrue(response_get.status_code == 403)
        self.assertFalse('<td>M\xc3\xa9thode de paiement</td>' in str(response_get.content))

class OperationTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.journal = GeneralJournal.objects.filter(id = 1).first()
        self.skia = User.objects.filter(username='skia').first()

    def test_new_operation(self):
        self.client.login(username='comptable', password='plop')  
        at = AccountingType.objects.filter(code = '604').first()
        response = self.client.post(reverse('accounting:op_new', 
                                                        args=[self.journal.id]),
                                                        {'amount': 30,
                                                        'remark' : "Un gros test",
                                                        'journal' : self.journal.id,
                                                        'target_type' : 'OTHER',
                                                        'target_id' : '',
                                                        'target_label' : "Le fantome de la nuit",
                                                        'date' : '04/12/2020',
                                                        'mode' : 'CASH',
                                                        'cheque_number' : '', 
                                                        'invoice' : '', 
                                                        'simpleaccounting_type' : '',
                                                        'accounting_type': at.id,
                                                        'label' : '',
                                                        'done' : False,
                                                        })
        self.assertFalse(response.status_code == 403)
        self.assertTrue(self.journal.operations.filter(target_label = "Le fantome de la nuit").exists())
        response_get = self.client.get(reverse("accounting:journal_details", args=[self.journal.id]))
        self.assertTrue('<td>Le fantome de la nuit</td>' in str(response_get.content))

    def test_bad_new_operation(self):
        self.client.login(username='comptable', password='plop')
        at = AccountingType.objects.filter(code = '604').first()
        response = self.client.post(reverse('accounting:op_new', 
                                                        args=[self.journal.id]),
                                                        {'amount': 30,
                                                        'remark' : "Un gros test",
                                                        'journal' : self.journal.id,
                                                        'target_type' : 'OTHER',
                                                        'target_id' : '',
                                                        'target_label' : "Le fantome de la nuit",
                                                        'date' : '04/12/2020',
                                                        'mode' : 'CASH',
                                                        'cheque_number' : '', 
                                                        'invoice' : '', 
                                                        'simpleaccounting_type' : '',
                                                        'accounting_type': '',
                                                        'label' : '',
                                                        'done' : False,
                                                        })
        self.assertTrue('Vous devez fournir soit un type comptable simplifi\\xc3\\xa9 ou un type comptable standard' in str(response.content))

    def test_new_operation_not_authorized(self):
        self.client.login(username='skia', password='plop')
        at = AccountingType.objects.filter(code = '604').first()
        response = self.client.post(reverse('accounting:op_new', 
                                                        args=[self.journal.id]),
                                                        {'amount': 30,
                                                        'remark' : "Un gros test",
                                                        'journal' : self.journal.id,
                                                        'target_type' : 'OTHER',
                                                        'target_id' : '',
                                                        'target_label' : "Le fantome du jour",
                                                        'date' : '04/12/2020',
                                                        'mode' : 'CASH',
                                                        'cheque_number' : '', 
                                                        'invoice' : '', 
                                                        'simpleaccounting_type' : '',
                                                        'accounting_type': at.id,
                                                        'label' : '',
                                                        'done' : False,
                                                        })
        self.assertTrue(response.status_code == 403)
        self.assertFalse(self.journal.operations.filter(target_label = "Le fantome du jour").exists())

    def test__operation_simple_accounting(self):
        self.client.login(username='comptable', password='plop')
        sat = SimplifiedAccountingType.objects.all().first()
        response = self.client.post(reverse('accounting:op_new', 
                                                        args=[self.journal.id]),
                                                        {'amount': 23,
                                                        'remark' : "Un gros test",
                                                        'journal' : self.journal.id,
                                                        'target_type' : 'OTHER',
                                                        'target_id' : '',
                                                        'target_label' : "Le fantome de l'aurore",
                                                        'date' : '04/12/2020',
                                                        'mode' : 'CASH',
                                                        'cheque_number' : '', 
                                                        'invoice' : '', 
                                                        'simpleaccounting_type' : sat.id,
                                                        'accounting_type': '',
                                                        'label' : '',
                                                        'done' : False,
                                                        })
        self.assertFalse(response.status_code == 403)
        self.assertTrue(self.journal.operations.filter(amount=23).exists())
        response_get = self.client.get(reverse("accounting:journal_details", args=[self.journal.id]))
        self.assertTrue("<td>Le fantome de l&#39;aurore</td>" in str(response_get.content))
        self.assertTrue(self.journal.operations.filter(amount=23).values('accounting_type').first()['accounting_type'] == AccountingType.objects.filter(code=6).values('id').first()['id'])