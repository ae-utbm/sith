# Generated by Django 1.11.20 on 2019-07-05 14:32
from __future__ import unicode_literals

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="UV",
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
                (
                    "code",
                    models.CharField(
                        max_length=10,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="The code of an UV must only contains uppercase characters without accent and numbers",
                                regex="([A-Z0-9]+)",
                            )
                        ],
                        verbose_name="code",
                    ),
                ),
                (
                    "credit_type",
                    models.CharField(
                        choices=[
                            ("FREE", "Free"),
                            ("CS", "CS"),
                            ("TM", "TM"),
                            ("OM", "OM"),
                            ("QC", "QC"),
                            ("EC", "EC"),
                            ("RN", "RN"),
                            ("ST", "ST"),
                            ("EXT", "EXT"),
                        ],
                        default="FREE",
                        max_length=10,
                        verbose_name="credit type",
                    ),
                ),
                (
                    "semester",
                    models.CharField(
                        choices=[
                            ("CLOSED", "Closed"),
                            ("AUTUMN", "Autumn"),
                            ("SPRING", "Spring"),
                            ("AUTUMN_AND_SPRING", "Autumn and spring"),
                        ],
                        default="CLOSED",
                        max_length=20,
                        verbose_name="semester",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("FR", "French"),
                            ("EN", "English"),
                            ("DE", "German"),
                            ("SP", "Spanich"),
                        ],
                        default="FR",
                        max_length=10,
                        verbose_name="language",
                    ),
                ),
                (
                    "credits",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="credits",
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
                        default="NA",
                        max_length=10,
                        verbose_name="departmenmt",
                    ),
                ),
                ("title", models.CharField(max_length=300, verbose_name="title")),
                (
                    "manager",
                    models.CharField(max_length=300, verbose_name="uv manager"),
                ),
                ("objectives", models.TextField(verbose_name="objectives")),
                ("program", models.TextField(verbose_name="program")),
                ("skills", models.TextField(verbose_name="skills")),
                ("key_concepts", models.TextField(verbose_name="key concepts")),
                (
                    "hours_CM",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="hours CM",
                    ),
                ),
                (
                    "hours_TD",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="hours TD",
                    ),
                ),
                (
                    "hours_TP",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="hours TP",
                    ),
                ),
                (
                    "hours_THE",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="hours THE",
                    ),
                ),
                (
                    "hours_TE",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="hours TE",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="uv_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="author",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UVComment",
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
                ("comment", models.TextField(blank=True, verbose_name="comment")),
                (
                    "grade_global",
                    models.IntegerField(
                        default=-1,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(4),
                        ],
                        verbose_name="global grade",
                    ),
                ),
                (
                    "grade_utility",
                    models.IntegerField(
                        default=-1,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(4),
                        ],
                        verbose_name="utility grade",
                    ),
                ),
                (
                    "grade_interest",
                    models.IntegerField(
                        default=-1,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(4),
                        ],
                        verbose_name="interest grade",
                    ),
                ),
                (
                    "grade_teaching",
                    models.IntegerField(
                        default=-1,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(4),
                        ],
                        verbose_name="teaching grade",
                    ),
                ),
                (
                    "grade_work_load",
                    models.IntegerField(
                        default=-1,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(4),
                        ],
                        verbose_name="work load grade",
                    ),
                ),
                (
                    "publish_date",
                    models.DateTimeField(blank=True, verbose_name="publish date"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="uv_comments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="author",
                    ),
                ),
                (
                    "uv",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="pedagogy.UV",
                        verbose_name="uv",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UVCommentReport",
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
                ("reason", models.TextField(verbose_name="reason")),
                (
                    "comment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reports",
                        to="pedagogy.UVComment",
                        verbose_name="report",
                    ),
                ),
                (
                    "reporter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reported_uv_comment",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="reporter",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UVResult",
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
                (
                    "grade",
                    models.CharField(
                        choices=[
                            ("A", "A"),
                            ("B", "B"),
                            ("C", "C"),
                            ("D", "D"),
                            ("E", "E"),
                            ("FX", "FX"),
                            ("F", "F"),
                            ("ABS", "Abs"),
                        ],
                        default="A",
                        max_length=10,
                        verbose_name="grade",
                    ),
                ),
                (
                    "semester",
                    models.CharField(
                        max_length=5,
                        validators=[
                            django.core.validators.RegexValidator("[AP][0-9]{3}")
                        ],
                        verbose_name="semester",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="uv_results",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
                (
                    "uv",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="pedagogy.UV",
                        verbose_name="uv",
                    ),
                ),
            ],
        ),
    ]
