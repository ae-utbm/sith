# Generated by Django 3.2.18 on 2023-05-10 12:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("counter", "0020_auto_20221215_1709"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cashregistersummaryitem",
            old_name="check",
            new_name="checked",
        ),
    ]
