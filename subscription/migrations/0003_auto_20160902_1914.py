# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("subscription", "0002_auto_20160830_1719")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="subscription_type",
            field=models.CharField(
                max_length=255,
                choices=[
                    ("amicale/doceo", "Amicale/DOCEO member"),
                    ("assidu", "Assidu member"),
                    ("crous", "CROUS member"),
                    ("cursus-alternant", "Alternating cursus"),
                    ("cursus-branche", "Branch cursus"),
                    ("cursus-tronc-commun", "Common core cursus"),
                    ("deux-semestres", "Two semesters"),
                    ("membre-honoraire", "Honorary member"),
                    ("reseau-ut", "UT network member"),
                    ("sbarro/esta", "Sbarro/ESTA member"),
                    ("un-semestre", "One semester"),
                ],
                verbose_name="subscription type",
            ),
        )
    ]
