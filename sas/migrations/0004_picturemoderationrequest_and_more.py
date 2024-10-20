# Generated by Django 4.2.16 on 2024-10-10 20:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sas", "0003_sasfile"),
    ]

    operations = [
        migrations.CreateModel(
            name="PictureModerationRequest",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "reason",
                    models.TextField(
                        default="",
                        help_text="Why do you want this image to be removed ?",
                        verbose_name="Reason",
                    ),
                ),
            ],
            options={
                "verbose_name": "Picture moderation request",
                "verbose_name_plural": "Picture moderation requests",
            },
        ),
        migrations.AddField(
            model_name="picturemoderationrequest",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="moderation_requests",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Author",
            ),
        ),
        migrations.AddField(
            model_name="picturemoderationrequest",
            name="picture",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="moderation_requests",
                to="sas.picture",
                verbose_name="Picture",
            ),
        ),
        migrations.AddConstraint(
            model_name="picturemoderationrequest",
            constraint=models.UniqueConstraint(
                fields=("author", "picture"), name="one_request_per_user_per_picture"
            ),
        ),
    ]
