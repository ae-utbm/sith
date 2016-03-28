# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0004_auto_20160321_1648'),
        ('core', '0001_initial'),
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('club', models.ForeignKey(to='club.Club', related_name='counters')),
                ('edit_groups', models.ManyToManyField(related_name='editable_counters', to='core.Group', blank=True)),
                ('products', models.ManyToManyField(related_name='counters', to='accounting.Product', blank=True)),
                ('view_groups', models.ManyToManyField(related_name='viewable_counters', to='core.Group', blank=True)),
            ],
        ),
    ]
