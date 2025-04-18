# Generated by Django 4.2.17 on 2024-12-09 11:07

from django.db import migrations, models

import counter.fields


class Migration(migrations.Migration):
    dependencies = [("counter", "0024_accountdump_accountdump_unique_ongoing_dump")]

    operations = [
        migrations.RemoveField(model_name="product", name="parent_product"),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(default="", verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="product",
            name="purchase_price",
            field=counter.fields.CurrencyField(
                decimal_places=2,
                help_text="Initial cost of purchasing the product",
                max_digits=12,
                verbose_name="purchase price",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="special_selling_price",
            field=counter.fields.CurrencyField(
                decimal_places=2,
                help_text="Price for barmen during their permanence",
                max_digits=12,
                verbose_name="special selling price",
            ),
        ),
    ]
