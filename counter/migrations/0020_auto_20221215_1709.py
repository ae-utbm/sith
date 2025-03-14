# Generated by Django 3.2.16 on 2022-12-15 16:09

from django.db import migrations

import counter.fields


class Migration(migrations.Migration):
    dependencies = [
        ("counter", "0019_billinginfo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="amount",
            field=counter.fields.CurrencyField(
                decimal_places=2, default=0, max_digits=12, verbose_name="amount"
            ),
        ),
    ]
