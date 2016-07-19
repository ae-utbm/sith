# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='payment_method',
            field=models.CharField(max_length=255, verbose_name='payment method', choices=[('cheque', 'Check'), ('cash', 'Cash'), ('other', 'Other')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(max_length=255, verbose_name='subscription type', choices=[('cursus-branche', 'Branch cursus'), ('cursus-tronc-commun', 'Common core cursus'), ('deux-semestres', 'Two semesters'), ('un-semestre', 'One semester')]),
        ),
    ]
