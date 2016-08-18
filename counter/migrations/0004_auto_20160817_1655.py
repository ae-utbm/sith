# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0003_auto_20160814_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='counter',
            name='type',
            field=models.CharField(choices=[('BAR', 'Bar'), ('OFFICE', 'Office'), ('EBOUTIC', 'Eboutic')], verbose_name='counter type', max_length=255),
        ),
        migrations.AlterField(
            model_name='refilling',
            name='bank',
            field=models.CharField(default='OTHER', choices=[('OTHER', 'Autre'), ('SOCIETE-GENERALE', 'Société générale'), ('BANQUE-POPULAIRE', 'Banque populaire'), ('BNP', 'BNP'), ('CAISSE-EPARGNE', "Caisse d'épargne"), ('CIC', 'CIC'), ('CREDIT-AGRICOLE', 'Crédit Agricole'), ('CREDIT-MUTUEL', 'Credit Mutuel'), ('CREDIT-LYONNAIS', 'Credit Lyonnais'), ('LA-POSTE', 'La Poste')], verbose_name='bank', max_length=255),
        ),
        migrations.AlterField(
            model_name='refilling',
            name='payment_method',
            field=models.CharField(default='CASH', choices=[('CHECK', 'Check'), ('CASH', 'Cash')], verbose_name='payment method', max_length=255),
        ),
    ]
