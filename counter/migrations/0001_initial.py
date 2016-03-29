# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
        ('accounting', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('type', models.CharField(max_length=255, verbose_name='subscription type', choices=[('BAR', 'Bar'), ('OFFICE', 'Office')])),
                ('club', models.ForeignKey(to='club.Club', related_name='counters')),
                ('edit_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='editable_counters')),
                ('products', models.ManyToManyField(to='accounting.Product', blank=True, related_name='counters')),
                ('view_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_counters')),
            ],
        ),
    ]
