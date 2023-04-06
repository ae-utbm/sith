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

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounting.models import (
    AccountingType,
    GeneralJournal,
    Label,
    Operation,
    SimplifiedAccountingType,
)
from core.models import User


class RefoundAccountTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skia = User.objects.get(username="skia")
        # reffil skia's account
        cls.skia.customer.amount = 800
        cls.skia.customer.save()
        cls.refound_account_url = reverse("accounting:refound_account")

    def test_permission_denied(self):
        self.client.force_login(User.objects.get(username="guy"))
        response_post = self.client.post(
            self.refound_account_url, {"user": self.skia.id}
        )
        response_get = self.client.get(self.refound_account_url)
        assert response_get.status_code == 403
        assert response_post.status_code == 403

    def test_root_granteed(self):
        self.client.force_login(User.objects.get(username="root"))
        response = self.client.post(self.refound_account_url, {"user": self.skia.id})
        self.assertRedirects(response, self.refound_account_url)
        self.skia.refresh_from_db()
        response = self.client.get(self.refound_account_url)
        assert response.status_code == 200
        assert '<form action="" method="post">' in str(response.content)
        assert self.skia.customer.amount == 0

    def test_comptable_granteed(self):
        self.client.force_login(User.objects.get(username="comptable"))
        response = self.client.post(self.refound_account_url, {"user": self.skia.id})
        self.assertRedirects(response, self.refound_account_url)
        self.skia.refresh_from_db()
        response = self.client.get(self.refound_account_url)
        assert response.status_code == 200
        assert '<form action="" method="post">' in str(response.content)
        assert self.skia.customer.amount == 0


class JournalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.journal = GeneralJournal.objects.get(id=1)

    def test_permission_granted(self):
        self.client.force_login(User.objects.get(username="comptable"))
        response_get = self.client.get(
            reverse("accounting:journal_details", args=[self.journal.id])
        )

        assert response_get.status_code == 200
        assert "<td>M\\xc3\\xa9thode de paiement</td>" in str(response_get.content)

    def test_permission_not_granted(self):
        self.client.force_login(User.objects.get(username="skia"))
        response_get = self.client.get(
            reverse("accounting:journal_details", args=[self.journal.id])
        )

        assert response_get.status_code == 403
        assert "<td>M\xc3\xa9thode de paiement</td>" not in str(response_get.content)


class OperationTest(TestCase):
    def setUp(self):
        self.tomorrow_formatted = (date.today() + timedelta(days=1)).strftime(
            "%d/%m/%Y"
        )
        self.journal = GeneralJournal.objects.filter(id=1).first()
        self.skia = User.objects.filter(username="skia").first()
        at = AccountingType(
            code="443", label="Ce code n'existe pas", movement_type="CREDIT"
        )
        at.save()
        l = Label.objects.create(club_account=self.journal.club_account, name="bob")
        self.client.force_login(User.objects.get(username="comptable"))
        self.op1 = Operation(
            journal=self.journal,
            date=date.today(),
            amount=1,
            remark="Test bilan",
            mode="CASH",
            done=True,
            label=l,
            accounting_type=at,
            target_type="USER",
            target_id=self.skia.id,
        )
        self.op1.save()
        self.op2 = Operation(
            journal=self.journal,
            date=date.today(),
            amount=2,
            remark="Test bilan",
            mode="CASH",
            done=True,
            label=l,
            accounting_type=at,
            target_type="USER",
            target_id=self.skia.id,
        )
        self.op2.save()

    def test_new_operation(self):
        at = AccountingType.objects.get(code="604")
        response = self.client.post(
            reverse("accounting:op_new", args=[self.journal.id]),
            {
                "amount": 30,
                "remark": "Un gros test",
                "journal": self.journal.id,
                "target_type": "OTHER",
                "target_id": "",
                "target_label": "Le fantome de la nuit",
                "date": self.tomorrow_formatted,
                "mode": "CASH",
                "cheque_number": "",
                "invoice": "",
                "simpleaccounting_type": "",
                "accounting_type": at.id,
                "label": "",
                "done": False,
            },
        )
        self.assertFalse(response.status_code == 403)
        self.assertTrue(
            self.journal.operations.filter(
                target_label="Le fantome de la nuit"
            ).exists()
        )
        response_get = self.client.get(
            reverse("accounting:journal_details", args=[self.journal.id])
        )
        self.assertTrue("<td>Le fantome de la nuit</td>" in str(response_get.content))

    def test_bad_new_operation(self):
        AccountingType.objects.get(code="604")
        response = self.client.post(
            reverse("accounting:op_new", args=[self.journal.id]),
            {
                "amount": 30,
                "remark": "Un gros test",
                "journal": self.journal.id,
                "target_type": "OTHER",
                "target_id": "",
                "target_label": "Le fantome de la nuit",
                "date": self.tomorrow_formatted,
                "mode": "CASH",
                "cheque_number": "",
                "invoice": "",
                "simpleaccounting_type": "",
                "accounting_type": "",
                "label": "",
                "done": False,
            },
        )
        self.assertTrue(
            "Vous devez fournir soit un type comptable simplifi\\xc3\\xa9 ou un type comptable standard"
            in str(response.content)
        )

    def test_new_operation_not_authorized(self):
        self.client.force_login(self.skia)
        at = AccountingType.objects.filter(code="604").first()
        response = self.client.post(
            reverse("accounting:op_new", args=[self.journal.id]),
            {
                "amount": 30,
                "remark": "Un gros test",
                "journal": self.journal.id,
                "target_type": "OTHER",
                "target_id": "",
                "target_label": "Le fantome du jour",
                "date": self.tomorrow_formatted,
                "mode": "CASH",
                "cheque_number": "",
                "invoice": "",
                "simpleaccounting_type": "",
                "accounting_type": at.id,
                "label": "",
                "done": False,
            },
        )
        self.assertTrue(response.status_code == 403)
        self.assertFalse(
            self.journal.operations.filter(target_label="Le fantome du jour").exists()
        )

    def test__operation_simple_accounting(self):
        sat = SimplifiedAccountingType.objects.all().first()
        response = self.client.post(
            reverse("accounting:op_new", args=[self.journal.id]),
            {
                "amount": 23,
                "remark": "Un gros test",
                "journal": self.journal.id,
                "target_type": "OTHER",
                "target_id": "",
                "target_label": "Le fantome de l'aurore",
                "date": self.tomorrow_formatted,
                "mode": "CASH",
                "cheque_number": "",
                "invoice": "",
                "simpleaccounting_type": sat.id,
                "accounting_type": "",
                "label": "",
                "done": False,
            },
        )
        self.assertFalse(response.status_code == 403)
        self.assertTrue(self.journal.operations.filter(amount=23).exists())
        response_get = self.client.get(
            reverse("accounting:journal_details", args=[self.journal.id])
        )
        self.assertTrue(
            "<td>Le fantome de l&#39;aurore</td>" in str(response_get.content)
        )
        self.assertTrue(
            self.journal.operations.filter(amount=23)
            .values("accounting_type")
            .first()["accounting_type"]
            == AccountingType.objects.filter(code=6).values("id").first()["id"]
        )

    def test_nature_statement(self):
        response = self.client.get(
            reverse("accounting:journal_nature_statement", args=[self.journal.id])
        )
        self.assertContains(response, "bob (Troll Penché) : 3.00", status_code=200)

    def test_person_statement(self):
        response = self.client.get(
            reverse("accounting:journal_person_statement", args=[self.journal.id])
        )
        self.assertContains(response, "Total : 5575.72", status_code=200)
        self.assertContains(response, "Total : 71.42")
        self.assertContains(
            response,
            """
                <td><a href="/user/1/">S&#39; Kia</a></td>
                
                <td>3.00</td>""",
        )
        self.assertContains(
            response,
            """
                <td><a href="/user/1/">S&#39; Kia</a></td>
                
                <td>823.00</td>""",
        )

    def test_accounting_statement(self):
        response = self.client.get(
            reverse("accounting:journal_accounting_statement", args=[self.journal.id])
        )
        self.assertContains(
            response,
            """
            <tr>
                <td>443 - Crédit - Ce code n&#39;existe pas</td>
                <td>3.00</td>
            </tr>""",
            status_code=200,
        )
        self.assertContains(
            response,
            """
    <p><strong>Montant : </strong>-5504.30 €</p>
    <p><strong>Montant effectif: </strong>-5504.30 €</p>""",
        )
