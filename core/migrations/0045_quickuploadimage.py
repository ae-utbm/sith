# Generated by Django 4.2.20 on 2025-04-10 08:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0044_alter_userban_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuickUploadImage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uuid", models.UUIDField(db_index=True, unique=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "image",
                    models.ImageField(
                        height_field="height",
                        upload_to="upload/%Y/%m/%d",
                        width_field="width",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created at"),
                ),
                ("width", models.PositiveIntegerField(verbose_name="width")),
                ("height", models.PositiveIntegerField(verbose_name="height")),
                ("size", models.PositiveIntegerField(verbose_name="size")),
                (
                    "uploader",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="quick_uploads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
