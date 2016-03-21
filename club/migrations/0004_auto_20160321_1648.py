# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0003_club_owner_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.IntegerField(choices=[(0, 'Curieux'), (1, 'Membre actif'), (2, 'Membre du bureau'), (3, 'Responsable info'), (4, 'Secrétaire'), (5, 'Responsable com'), (7, 'Trésorier'), (9, 'Vice-Président'), (10, 'Président')], default=0, verbose_name='role'),
        ),
    ]
