# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0001_initial"),
        ("accounting", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="operation",
            name="invoice",
            field=models.ForeignKey(
                null=True,
                related_name="operations",
                verbose_name="invoice",
                to="core.SithFile",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="operation",
            name="journal",
            field=models.ForeignKey(
                verbose_name="journal",
                to="accounting.GeneralJournal",
                related_name="operations",
            ),
        ),
        migrations.AddField(
            model_name="operation",
            name="linked_operation",
            field=models.OneToOneField(
                blank=True,
                to="accounting.Operation",
                null=True,
                related_name="operation_linked_to",
                verbose_name="linked operation",
                default=None,
            ),
        ),
        migrations.AddField(
            model_name="operation",
            name="simpleaccounting_type",
            field=models.ForeignKey(
                null=True,
                related_name="operations",
                verbose_name="simple type",
                to="accounting.SimplifiedAccountingType",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="generaljournal",
            name="club_account",
            field=models.ForeignKey(
                verbose_name="club account",
                to="accounting.ClubAccount",
                related_name="journals",
            ),
        ),
        migrations.AddField(
            model_name="clubaccount",
            name="bank_account",
            field=models.ForeignKey(
                verbose_name="bank account",
                to="accounting.BankAccount",
                related_name="club_accounts",
            ),
        ),
        migrations.AddField(
            model_name="clubaccount",
            name="club",
            field=models.ForeignKey(
                verbose_name="club", to="club.Club", related_name="club_account"
            ),
        ),
        migrations.AddField(
            model_name="bankaccount",
            name="club",
            field=models.ForeignKey(
                verbose_name="club", to="club.Club", related_name="bank_accounts"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="operation", unique_together=set([("number", "journal")])
        ),
    ]
