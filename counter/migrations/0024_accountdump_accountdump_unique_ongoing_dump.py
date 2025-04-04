# Generated by Django 4.2.16 on 2024-10-06 14:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("counter", "0023_billinginfo_phone_number")]

    operations = [
        migrations.CreateModel(
            name="AccountDump",
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
                    "warning_mail_sent_at",
                    models.DateTimeField(
                        help_text="When the mail warning that the account was about to be dumped was sent."
                    ),
                ),
                (
                    "warning_mail_error",
                    models.BooleanField(
                        default=False,
                        help_text="Set this to True if the warning mail received an error",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dumps",
                        to="counter.customer",
                    ),
                ),
                (
                    "dump_operation",
                    models.OneToOneField(
                        blank=True,
                        help_text="The operation that emptied the account.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="counter.selling",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="accountdump",
            constraint=models.UniqueConstraint(
                condition=models.Q(("dump_operation", None)),
                fields=("customer",),
                name="unique_ongoing_dump",
            ),
        ),
    ]
