from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("club", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                verbose_name="user",
                to=settings.AUTH_USER_MODEL,
                related_name="membership",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="edit_groups",
            field=models.ManyToManyField(
                to="core.Group", blank=True, related_name="editable_club"
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="home",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                blank=True,
                null=True,
                related_name="home_of_club",
                verbose_name="home",
                to="core.SithFile",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="owner_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                default=1,
                to="core.Group",
                related_name="owned_club",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="parent",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                to="club.Club",
                related_name="children",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="view_groups",
            field=models.ManyToManyField(
                to="core.Group", blank=True, related_name="viewable_club"
            ),
        ),
    ]
