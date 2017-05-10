# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0007_auto_20170324_0917'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trombi',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('subscription_deadline', models.DateField(verbose_name='subscription deadline', default=django.utils.timezone.now, help_text='Before this date, users are allowed to subscribe to this Trombi. After this date, users subscribed will be allowed to comment on each other.')),
                ('comments_deadline', models.DateField(verbose_name='comments deadline', default=django.utils.timezone.now, help_text="After this date, users won't be able to make comments anymore")),
                ('max_chars', models.IntegerField(verbose_name='maximum characters', default=400, help_text='maximum number of characters allowed in a comment')),
                ('club', models.OneToOneField(to='club.Club', related_name='trombi')),
            ],
        ),
        migrations.CreateModel(
            name='TrombiComment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('content', models.TextField(verbose_name='content', default='')),
            ],
        ),
        migrations.CreateModel(
            name='TrombiUser',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('trombi', models.ForeignKey(to='trombi.Trombi', related_name='users', verbose_name='trombi', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='trombi_user', verbose_name='trombi user')),
            ],
        ),
        migrations.AddField(
            model_name='trombicomment',
            name='author',
            field=models.ForeignKey(to='trombi.TrombiUser', related_name='given_comments', verbose_name='author'),
        ),
        migrations.AddField(
            model_name='trombicomment',
            name='target',
            field=models.ForeignKey(to='trombi.TrombiUser', related_name='received_comments', verbose_name='target'),
        ),
    ]
