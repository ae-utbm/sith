# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ae', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(verbose_name='subscription type', max_length=255, choices=[('cursus-branche', 'Cursus Branche'), ('cursus-tronc-commun', 'Cursus Tronc Commun'), ('deux-semestres', 'Deux semestres'), ('un-semestre', 'Un semestre')]),
        ),
    ]
