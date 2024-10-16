# Generated by Django 4.2.16 on 2024-09-18 11:33

from django.db import migrations

# This migration is here only to delete all the models
# of the stock application and will be removed in a subsequent release


class Migration(migrations.Migration):
    dependencies = [
        ("stock", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="shoppinglistitem",
            name="shopping_lists",
        ),
        migrations.RemoveField(
            model_name="shoppinglistitem",
            name="stockitem_owner",
        ),
        migrations.RemoveField(
            model_name="shoppinglistitem",
            name="type",
        ),
        migrations.RemoveField(
            model_name="stock",
            name="counter",
        ),
        migrations.RemoveField(
            model_name="stockitem",
            name="stock_owner",
        ),
        migrations.RemoveField(
            model_name="stockitem",
            name="type",
        ),
        migrations.DeleteModel(
            name="ShoppingList",
        ),
        migrations.DeleteModel(
            name="ShoppingListItem",
        ),
        migrations.DeleteModel(
            name="Stock",
        ),
        migrations.DeleteModel(
            name="StockItem",
        ),
    ]
