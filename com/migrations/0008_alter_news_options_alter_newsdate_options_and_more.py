# Generated by Django 4.2.17 on 2025-01-06 21:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("com", "0007_alter_news_club_alter_news_content_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="news",
            options={
                "verbose_name": "news",
                "permissions": [
                    ("moderate_news", "Can moderate news"),
                    ("view_unmoderated_news", "Can view non-moderated news"),
                ],
            },
        ),
        migrations.AlterModelOptions(
            name="newsdate",
            options={"verbose_name": "news date", "verbose_name_plural": "news dates"},
        ),
        migrations.AlterModelOptions(
            name="poster",
            options={"permissions": [("moderate_poster", "Can moderate poster")]},
        ),
        migrations.RemoveField(model_name="news", name="type"),
        migrations.AlterField(
            model_name="news",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_news",
                to=settings.AUTH_USER_MODEL,
                verbose_name="author",
            ),
        ),
        migrations.AlterField(
            model_name="newsdate",
            name="end_date",
            field=models.DateTimeField(verbose_name="end_date"),
        ),
        migrations.AlterField(
            model_name="newsdate",
            name="start_date",
            field=models.DateTimeField(verbose_name="start_date"),
        ),
        migrations.AddConstraint(
            model_name="newsdate",
            constraint=models.CheckConstraint(
                check=models.Q(("end_date__gte", models.F("start_date"))),
                name="news_date_end_date_after_start_date",
            ),
        ),
    ]
