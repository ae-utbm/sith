# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("subscription", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0001_initial"),
        ("club", "0002_auto_20160824_2152"),
    ]

    operations = [
        migrations.CreateModel(
            name="Counter",
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
                ("name", models.CharField(max_length=30, verbose_name="name")),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("BAR", "Bar"),
                            ("OFFICE", "Office"),
                            ("EBOUTIC", "Eboutic"),
                        ],
                        max_length=255,
                        verbose_name="counter type",
                    ),
                ),
                ("club", models.ForeignKey(to="club.Club", related_name="counters")),
                (
                    "edit_groups",
                    models.ManyToManyField(
                        to="core.Group", blank=True, related_name="editable_counters"
                    ),
                ),
            ],
            options={"verbose_name": "counter"},
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "account_id",
                    models.CharField(
                        unique=True, max_length=10, verbose_name="account id"
                    ),
                ),
                (
                    "amount",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="amount"
                    ),
                ),
            ],
            options={
                "verbose_name": "customer",
                "ordering": ["account_id"],
                "verbose_name_plural": "customers",
            },
        ),
        migrations.CreateModel(
            name="Permanency",
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
                ("start", models.DateTimeField(verbose_name="start date")),
                ("end", models.DateTimeField(verbose_name="end date")),
                (
                    "counter",
                    models.ForeignKey(
                        to="counter.Counter", related_name="permanencies"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, related_name="permanencies"
                    ),
                ),
            ],
            options={"verbose_name": "permanency"},
        ),
        migrations.CreateModel(
            name="Product",
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
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                (
                    "code",
                    models.CharField(max_length=16, blank=True, verbose_name="code"),
                ),
                (
                    "purchase_price",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="purchase price"
                    ),
                ),
                (
                    "selling_price",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="selling price"
                    ),
                ),
                (
                    "special_selling_price",
                    accounting.models.CurrencyField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="special selling price",
                    ),
                ),
                (
                    "icon",
                    models.ImageField(
                        upload_to="products", null=True, verbose_name="icon", blank=True
                    ),
                ),
                ("limit_age", models.IntegerField(default=0, verbose_name="limit age")),
                ("tray", models.BooleanField(verbose_name="tray price", default=False)),
                (
                    "buying_groups",
                    models.ManyToManyField(
                        related_name="products",
                        to="core.Group",
                        verbose_name="buying groups",
                    ),
                ),
                (
                    "club",
                    models.ForeignKey(
                        verbose_name="club", to="club.Club", related_name="products"
                    ),
                ),
                (
                    "parent_product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        related_name="children_products",
                        verbose_name="parent product",
                        to="counter.Product",
                        blank=True,
                    ),
                ),
            ],
            options={"verbose_name": "product"},
        ),
        migrations.CreateModel(
            name="ProductType",
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
                ("name", models.CharField(max_length=30, verbose_name="name")),
                (
                    "description",
                    models.TextField(null=True, verbose_name="description", blank=True),
                ),
                (
                    "icon",
                    models.ImageField(upload_to="products", null=True, blank=True),
                ),
            ],
            options={"verbose_name": "product type"},
        ),
        migrations.CreateModel(
            name="Refilling",
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
                    "amount",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="amount"
                    ),
                ),
                ("date", models.DateTimeField(verbose_name="date")),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("CHECK", "Check"),
                            ("CASH", "Cash"),
                            ("CARD", "Credit card"),
                        ],
                        max_length=255,
                        default="CASH",
                        verbose_name="payment method",
                    ),
                ),
                (
                    "bank",
                    models.CharField(
                        choices=[
                            ("OTHER", "Autre"),
                            ("SOCIETE-GENERALE", "Société générale"),
                            ("BANQUE-POPULAIRE", "Banque populaire"),
                            ("BNP", "BNP"),
                            ("CAISSE-EPARGNE", "Caisse d'épargne"),
                            ("CIC", "CIC"),
                            ("CREDIT-AGRICOLE", "Crédit Agricole"),
                            ("CREDIT-MUTUEL", "Credit Mutuel"),
                            ("CREDIT-LYONNAIS", "Credit Lyonnais"),
                            ("LA-POSTE", "La Poste"),
                        ],
                        max_length=255,
                        default="OTHER",
                        verbose_name="bank",
                    ),
                ),
                (
                    "is_validated",
                    models.BooleanField(verbose_name="is validated", default=False),
                ),
                (
                    "counter",
                    models.ForeignKey(to="counter.Counter", related_name="refillings"),
                ),
                (
                    "customer",
                    models.ForeignKey(to="counter.Customer", related_name="refillings"),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        related_name="refillings_as_operator",
                    ),
                ),
            ],
            options={"verbose_name": "refilling"},
        ),
        migrations.CreateModel(
            name="Selling",
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
                ("label", models.CharField(max_length=64, verbose_name="label")),
                (
                    "unit_price",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="unit price"
                    ),
                ),
                ("quantity", models.IntegerField(verbose_name="quantity")),
                ("date", models.DateTimeField(verbose_name="date")),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("SITH_ACCOUNT", "Sith account"),
                            ("CARD", "Credit card"),
                        ],
                        max_length=255,
                        default="SITH_ACCOUNT",
                        verbose_name="payment method",
                    ),
                ),
                (
                    "is_validated",
                    models.BooleanField(verbose_name="is validated", default=False),
                ),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        to="club.Club",
                        related_name="sellings",
                    ),
                ),
                (
                    "counter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        to="counter.Counter",
                        related_name="sellings",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        to="counter.Customer",
                        related_name="buyings",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        to="counter.Product",
                        related_name="sellings",
                        blank=True,
                    ),
                ),
                (
                    "seller",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        related_name="sellings_as_operator",
                    ),
                ),
            ],
            options={"verbose_name": "selling"},
        ),
        migrations.AddField(
            model_name="product",
            name="product_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name="products",
                verbose_name="product type",
                to="counter.ProductType",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="counter",
            name="products",
            field=models.ManyToManyField(
                to="counter.Product", blank=True, related_name="counters"
            ),
        ),
        migrations.AddField(
            model_name="counter",
            name="sellers",
            field=models.ManyToManyField(
                related_name="counters",
                to="core.User",
                blank=True,
                verbose_name="sellers",
            ),
        ),
        migrations.AddField(
            model_name="counter",
            name="view_groups",
            field=models.ManyToManyField(
                to="core.Group", blank=True, related_name="viewable_counters"
            ),
        ),
    ]
