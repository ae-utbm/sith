# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.auth.models
import django.db.models.deletion
import django.core.validators
import core.models
import phonenumber_field.modelfields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [("auth", "0006_require_contenttypes_0002")]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        null=True, verbose_name="last login", blank=True
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        help_text="Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        unique=True,
                        max_length=254,
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        verbose_name="username",
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[\\w.@+-]+$",
                                "Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.",
                            )
                        ],
                    ),
                ),
                (
                    "first_name",
                    models.CharField(max_length=64, verbose_name="first name"),
                ),
                (
                    "last_name",
                    models.CharField(max_length=64, verbose_name="last name"),
                ),
                (
                    "email",
                    models.EmailField(
                        unique=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "date_of_birth",
                    models.DateField(
                        null=True, verbose_name="date of birth", blank=True
                    ),
                ),
                (
                    "nick_name",
                    models.CharField(
                        max_length=64, null=True, verbose_name="nick name", blank=True
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                        default=False,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                        default=True,
                    ),
                ),
                (
                    "date_joined",
                    models.DateField(auto_now_add=True, verbose_name="date joined"),
                ),
                (
                    "last_update",
                    models.DateField(verbose_name="last update", auto_now=True),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        help_text="Designates whether this user is a superuser. ",
                        verbose_name="superuser",
                        default=False,
                    ),
                ),
                (
                    "sex",
                    models.CharField(
                        choices=[("MAN", "Man"), ("WOMAN", "Woman")],
                        max_length=10,
                        default="MAN",
                        verbose_name="sex",
                    ),
                ),
                (
                    "tshirt_size",
                    models.CharField(
                        choices=[
                            ("-", "-"),
                            ("XS", "XS"),
                            ("S", "S"),
                            ("M", "M"),
                            ("L", "L"),
                            ("XL", "XL"),
                            ("XXL", "XXL"),
                            ("XXXL", "XXXL"),
                        ],
                        max_length=5,
                        default="-",
                        verbose_name="tshirt size",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("STUDENT", "Student"),
                            ("ADMINISTRATIVE", "Administrative agent"),
                            ("TEACHER", "Teacher"),
                            ("AGENT", "Agent"),
                            ("DOCTOR", "Doctor"),
                            ("FORMER STUDENT", "Former student"),
                            ("SERVICE", "Service"),
                        ],
                        max_length=15,
                        blank=True,
                        verbose_name="role",
                        default="",
                    ),
                ),
                (
                    "department",
                    models.CharField(
                        choices=[
                            ("TC", "TC"),
                            ("IMSI", "IMSI"),
                            ("IMAP", "IMAP"),
                            ("INFO", "INFO"),
                            ("GI", "GI"),
                            ("E", "E"),
                            ("EE", "EE"),
                            ("GESC", "GESC"),
                            ("GMC", "GMC"),
                            ("MC", "MC"),
                            ("EDIM", "EDIM"),
                            ("HUMA", "Humanities"),
                            ("NA", "N/A"),
                        ],
                        max_length=15,
                        blank=True,
                        verbose_name="department",
                        default="NA",
                    ),
                ),
                (
                    "dpt_option",
                    models.CharField(
                        max_length=32, blank=True, verbose_name="dpt option", default=""
                    ),
                ),
                (
                    "semester",
                    models.CharField(
                        max_length=5, blank=True, verbose_name="semester", default=""
                    ),
                ),
                (
                    "quote",
                    models.CharField(
                        max_length=256, blank=True, verbose_name="quote", default=""
                    ),
                ),
                (
                    "school",
                    models.CharField(
                        max_length=80, blank=True, verbose_name="school", default=""
                    ),
                ),
                (
                    "promo",
                    models.IntegerField(
                        null=True,
                        verbose_name="promo",
                        validators=[core.models.validate_promo],
                        blank=True,
                    ),
                ),
                (
                    "forum_signature",
                    models.TextField(
                        max_length=256,
                        blank=True,
                        verbose_name="forum signature",
                        default="",
                    ),
                ),
                (
                    "second_email",
                    models.EmailField(
                        max_length=254,
                        null=True,
                        verbose_name="second email address",
                        blank=True,
                    ),
                ),
                (
                    "phone",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, null=True, verbose_name="phone", blank=True
                    ),
                ),
                (
                    "parent_phone",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128,
                        null=True,
                        verbose_name="parent phone",
                        blank=True,
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        max_length=128, blank=True, verbose_name="address", default=""
                    ),
                ),
                (
                    "parent_address",
                    models.CharField(
                        max_length=128,
                        blank=True,
                        verbose_name="parent address",
                        default="",
                    ),
                ),
                (
                    "is_subscriber_viewable",
                    models.BooleanField(
                        verbose_name="is subscriber viewable", default=True
                    ),
                ),
            ],
            options={"abstract": False},
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name="Group",
            fields=[
                (
                    "group_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        parent_link=True,
                        serialize=False,
                        to="auth.Group",
                        auto_created=True,
                    ),
                ),
                (
                    "is_meta",
                    models.BooleanField(
                        help_text="Whether a group is a meta group or not",
                        verbose_name="meta group status",
                        default=False,
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=60, verbose_name="description"),
                ),
            ],
            bases=("auth.group",),
        ),
        migrations.CreateModel(
            name="Page",
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
                ("name", models.CharField(max_length=30, verbose_name="page name")),
                (
                    "_full_name",
                    models.CharField(
                        max_length=255, blank=True, verbose_name="page name"
                    ),
                ),
                (
                    "edit_groups",
                    models.ManyToManyField(
                        related_name="editable_page",
                        to="core.Group",
                        blank=True,
                        verbose_name="edit group",
                    ),
                ),
                (
                    "owner_group",
                    models.ForeignKey(
                        default=1,
                        related_name="owned_page",
                        verbose_name="owner group",
                        to="core.Group",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        related_name="children",
                        verbose_name="parent",
                        to="core.Page",
                        blank=True,
                    ),
                ),
                (
                    "view_groups",
                    models.ManyToManyField(
                        related_name="viewable_page",
                        to="core.Group",
                        blank=True,
                        verbose_name="view group",
                    ),
                ),
            ],
            options={
                "permissions": (
                    (
                        "change_prop_page",
                        "Can change the page's properties (groups, ...)",
                    ),
                    ("view_page", "Can view the page"),
                )
            },
        ),
        migrations.CreateModel(
            name="PageRev",
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
                ("revision", models.IntegerField(verbose_name="revision")),
                (
                    "title",
                    models.CharField(
                        max_length=255, blank=True, verbose_name="page title"
                    ),
                ),
                ("content", models.TextField(blank=True, verbose_name="page content")),
                ("date", models.DateTimeField(verbose_name="date", auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, related_name="page_rev"
                    ),
                ),
                ("page", models.ForeignKey(to="core.Page", related_name="revisions")),
            ],
            options={"ordering": ["date"]},
        ),
        migrations.CreateModel(
            name="Preferences",
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
                    "show_my_stats",
                    models.BooleanField(
                        help_text="Show your account statistics to others",
                        verbose_name="define if we show a users stats",
                        default=False,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        to=settings.AUTH_USER_MODEL, related_name="preferences"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SithFile",
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
                ("name", models.CharField(max_length=30, verbose_name="file name")),
                (
                    "file",
                    models.FileField(
                        upload_to=core.models.get_directory,
                        null=True,
                        verbose_name="file",
                        blank=True,
                    ),
                ),
                (
                    "is_folder",
                    models.BooleanField(verbose_name="is folder", default=True),
                ),
                (
                    "mime_type",
                    models.CharField(max_length=30, verbose_name="mime type"),
                ),
                ("size", models.IntegerField(default=0, verbose_name="size")),
                ("date", models.DateTimeField(verbose_name="date", auto_now=True)),
                (
                    "edit_groups",
                    models.ManyToManyField(
                        related_name="editable_files",
                        to="core.Group",
                        blank=True,
                        verbose_name="edit group",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        verbose_name="owner",
                        to=settings.AUTH_USER_MODEL,
                        related_name="owned_files",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        null=True,
                        related_name="children",
                        verbose_name="parent",
                        to="core.SithFile",
                        blank=True,
                    ),
                ),
                (
                    "view_groups",
                    models.ManyToManyField(
                        related_name="viewable_files",
                        to="core.Group",
                        blank=True,
                        verbose_name="view group",
                    ),
                ),
            ],
            options={"verbose_name": "file"},
        ),
        migrations.AddField(
            model_name="user",
            name="avatar_pict",
            field=models.OneToOneField(
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name="avatar_of",
                verbose_name="avatar",
                to="core.SithFile",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="home",
            field=models.OneToOneField(
                blank=True,
                null=True,
                related_name="home_of",
                verbose_name="home",
                to="core.SithFile",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="profile_pict",
            field=models.OneToOneField(
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name="profile_of",
                verbose_name="profile",
                to="core.SithFile",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="scrub_pict",
            field=models.OneToOneField(
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name="scrub_of",
                verbose_name="scrub",
                to="core.SithFile",
            ),
        ),
        migrations.CreateModel(
            name="MetaGroup",
            fields=[],
            options={"proxy": True},
            bases=("core.group",),
            managers=[("objects", core.models.MetaGroupManager())],
        ),
        migrations.CreateModel(
            name="RealGroup",
            fields=[],
            options={"proxy": True},
            bases=("core.group",),
            managers=[("objects", core.models.RealGroupManager())],
        ),
        migrations.AlterUniqueTogether(
            name="page", unique_together=set([("name", "parent")])
        ),
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(
                to="core.RealGroup", blank=True, related_name="users"
            ),
        ),
    ]
