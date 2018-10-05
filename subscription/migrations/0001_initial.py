# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "subscription_type",
                    models.CharField(
                        choices=[
                            ("amicale/doceo", "Amicale/DOCEO member"),
                            ("assidu", "Assidu member"),
                            ("crous", "CROUS member"),
                            ("cursus-alternant", "Branch cursus"),
                            ("cursus-branche", "Branch cursus"),
                            ("cursus-tronc-commun", "Common core cursus"),
                            ("deux-semestres", "Two semesters"),
                            ("membre-honoraire", "Honorary member"),
                            ("reseau-ut", "UT network member"),
                            ("sbarro/esta", "Sbarro/ESTA member"),
                            ("un-semestre", "One semester"),
                        ],
                        max_length=255,
                        verbose_name="subscription type",
                    ),
                ),
                (
                    "subscription_start",
                    models.DateField(verbose_name="subscription start"),
                ),
                ("subscription_end", models.DateField(verbose_name="subscription end")),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("CHECK", "Check"),
                            ("CARD", "Credit card"),
                            ("CASH", "Cash"),
                            ("EBOUTIC", "Eboutic"),
                            ("OTHER", "Other"),
                        ],
                        max_length=255,
                        verbose_name="payment method",
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        choices=[
                            ("BELFORT", "Belfort"),
                            ("SEVENANS", "Sevenans"),
                            ("MONTBELIARD", "Montbéliard"),
                        ],
                        max_length=20,
                        verbose_name="location",
                    ),
                ),
            ],
            options={"ordering": ["subscription_start"]},
        ),
        migrations.AddField(
            model_name="subscription",
            name="member",
            field=models.ForeignKey(to="core.User", related_name="subscriptions"),
        ),
    ]
