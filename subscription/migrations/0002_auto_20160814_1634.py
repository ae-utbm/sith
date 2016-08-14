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
            field=models.CharField(verbose_name='payment method', max_length=255, choices=[('CHECK', 'Check'), ('CARD', 'Credit card'), ('CASH', 'Cash'), ('EBOUTIC', 'Eboutic'), ('OTHER', 'Other')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(verbose_name='subscription type', max_length=255, choices=[('amicale/doceo', 'Amicale/DOCEO member'), ('assidu', 'Assidu member'), ('crous', 'CROUS member'), ('cursus-alternant', 'Branch cursus'), ('cursus-branche', 'Branch cursus'), ('cursus-tronc-commun', 'Common core cursus'), ('deux-semestres', 'Two semesters'), ('membre-honoraire', 'Honorary member'), ('reseau-ut', 'UT network member'), ('sbarro/esta', 'Sbarro/ESTA member'), ('un-semestre', 'One semester')]),
        ),
    ]
