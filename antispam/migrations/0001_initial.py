# Generated by Django 4.2.14 on 2024-08-03 23:05

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ToxicDomain",
            fields=[
                (
                    "domain",
                    models.URLField(
                        max_length=253,
                        primary_key=True,
                        serialize=False,
                        verbose_name="domain",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "is_externally_managed",
                    models.BooleanField(
                        default=False,
                        help_text="True if kept up-to-date using external toxic domain providers, else False",
                        verbose_name="is externally managed",
                    ),
                ),
            ],
        ),
    ]
