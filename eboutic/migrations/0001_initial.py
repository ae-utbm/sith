from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import counter.fields


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Basket",
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
                ("date", models.DateTimeField(verbose_name="date", auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="user",
                        to=settings.AUTH_USER_MODEL,
                        related_name="baskets",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BasketItem",
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
                ("product_id", models.IntegerField(verbose_name="product id")),
                (
                    "product_name",
                    models.CharField(max_length=255, verbose_name="product name"),
                ),
                ("type_id", models.IntegerField(verbose_name="product type id")),
                (
                    "product_unit_price",
                    counter.fields.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="unit price"
                    ),
                ),
                ("quantity", models.IntegerField(verbose_name="quantity")),
                (
                    "basket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="basket",
                        to="eboutic.Basket",
                        related_name="items",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Invoice",
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
                ("date", models.DateTimeField(verbose_name="date", auto_now=True)),
                (
                    "validated",
                    models.BooleanField(verbose_name="validated", default=False),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="user",
                        to=settings.AUTH_USER_MODEL,
                        related_name="invoices",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InvoiceItem",
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
                ("product_id", models.IntegerField(verbose_name="product id")),
                (
                    "product_name",
                    models.CharField(max_length=255, verbose_name="product name"),
                ),
                ("type_id", models.IntegerField(verbose_name="product type id")),
                (
                    "product_unit_price",
                    counter.fields.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="unit price"
                    ),
                ),
                ("quantity", models.IntegerField(verbose_name="quantity")),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="invoice",
                        to="eboutic.Invoice",
                        related_name="items",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
