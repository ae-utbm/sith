# Generated by Django 3.2.18 on 2023-05-10 12:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pedagogy", "0002_auto_20190827_2251"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uv",
            name="language",
            field=models.CharField(
                choices=[
                    ("FR", "French"),
                    ("EN", "English"),
                    ("DE", "German"),
                    ("SP", "Spanish"),
                ],
                default="FR",
                max_length=10,
                verbose_name="language",
            ),
        ),
    ]
