# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("counter", "0011_auto_20161004_2039")]

    operations = [
        migrations.CreateModel(
            name="ShoppingList",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("date", models.DateTimeField(verbose_name="date")),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                ("todo", models.BooleanField(verbose_name="todo")),
                (
                    "comment",
                    models.TextField(verbose_name="comment", blank=True, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ShoppingListItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "tobuy_quantity",
                    models.IntegerField(
                        verbose_name="quantity to buy",
                        help_text="quantity to buy during the next shopping session",
                        default=6,
                    ),
                ),
                (
                    "bought_quantity",
                    models.IntegerField(
                        verbose_name="quantity bought",
                        help_text="quantity bought during the last shopping session",
                        default=0,
                    ),
                ),
                (
                    "shopping_lists",
                    models.ManyToManyField(
                        verbose_name="shopping lists",
                        related_name="shopping_items_to_buy",
                        to="stock.ShoppingList",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Stock",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "counter",
                    models.OneToOneField(
                        verbose_name="counter",
                        related_name="stock",
                        to="counter.Counter",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StockItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "unit_quantity",
                    models.IntegerField(
                        verbose_name="unit quantity",
                        help_text="number of element in one box",
                        default=0,
                    ),
                ),
                (
                    "effective_quantity",
                    models.IntegerField(
                        verbose_name="effective quantity",
                        help_text="number of box",
                        default=0,
                    ),
                ),
                (
                    "minimal_quantity",
                    models.IntegerField(
                        verbose_name="minimal quantity",
                        help_text="if the effective quantity is less than the minimal, item is added to the shopping list",
                        default=1,
                    ),
                ),
                (
                    "stock_owner",
                    models.ForeignKey(related_name="items", to="stock.Stock"),
                ),
                (
                    "type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        verbose_name="type",
                        related_name="stock_items",
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="counter.ProductType",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="shoppinglistitem",
            name="stockitem_owner",
            field=models.ForeignKey(
                null=True, related_name="shopping_item", to="stock.StockItem"
            ),
        ),
        migrations.AddField(
            model_name="shoppinglistitem",
            name="type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                verbose_name="type",
                related_name="shoppinglist_items",
                on_delete=django.db.models.deletion.SET_NULL,
                to="counter.ProductType",
            ),
        ),
        migrations.AddField(
            model_name="shoppinglist",
            name="stock_owner",
            field=models.ForeignKey(
                null=True, related_name="shopping_lists", to="stock.Stock"
            ),
        ),
    ]
