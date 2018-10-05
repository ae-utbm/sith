# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [("accounting", "0002_auto_20160824_2152")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="city",
            field=models.CharField(blank=True, verbose_name="city", max_length=60),
        ),
        migrations.AddField(
            model_name="company",
            name="country",
            field=models.CharField(blank=True, verbose_name="country", max_length=32),
        ),
        migrations.AddField(
            model_name="company",
            name="email",
            field=models.EmailField(blank=True, verbose_name="email", max_length=254),
        ),
        migrations.AddField(
            model_name="company",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, verbose_name="phone", max_length=128
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="postcode",
            field=models.CharField(blank=True, verbose_name="postcode", max_length=10),
        ),
        migrations.AddField(
            model_name="company",
            name="street",
            field=models.CharField(blank=True, verbose_name="street", max_length=60),
        ),
        migrations.AddField(
            model_name="company",
            name="website",
            field=models.CharField(blank=True, verbose_name="website", max_length=64),
        ),
    ]
