# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matmat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='matmat',
            name='max_chars',
            field=models.IntegerField(help_text='maximum number of characters allowed in a comment', default=400, verbose_name='maximum characters'),
        ),
        migrations.AddField(
            model_name='matmatcomment',
            name='content',
            field=models.TextField(default='', verbose_name='content'),
        ),
        migrations.AddField(
            model_name='matmatcomment',
            name='is_moderated',
            field=models.BooleanField(default=False, verbose_name='is moderated'),
        ),
        migrations.AddField(
            model_name='matmatcomment',
            name='target',
            field=models.ForeignKey(verbose_name='target', to='matmat.MatmatUser', related_name='received_comments', default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='matmatcomment',
            name='author',
            field=models.ForeignKey(verbose_name='author', to='matmat.MatmatUser', related_name='given_comments', default=0),
            preserve_default=False,
        ),
    ]
