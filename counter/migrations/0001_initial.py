# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
        ('core', '0001_initial'),
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('type', models.CharField(max_length=255, verbose_name='subscription type', choices=[('BAR', 'Bar'), ('OFFICE', 'Office')])),
                ('club', models.ForeignKey(to='club.Club', related_name='counters')),
                ('edit_groups', models.ManyToManyField(blank=True, related_name='editable_counters', to='core.Group')),
                ('products', models.ManyToManyField(blank=True, related_name='counters', to='accounting.Product')),
                ('view_groups', models.ManyToManyField(blank=True, related_name='viewable_counters', to='core.Group')),
            ],
        ),
    ]
