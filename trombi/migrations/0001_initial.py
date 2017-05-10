# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0007_auto_20170324_0917'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trombi',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('subscription_deadline', models.DateField(help_text='Before this date, users are allowed to subscribe to this Trombi. After this date, users subscribed will be allowed to comment on each other.', default=django.utils.timezone.now, verbose_name='subscription deadline')),
                ('comments_deadline', models.DateField(help_text="After this date, users won't be able to make comments anymore.", default=django.utils.timezone.now, verbose_name='comments deadline')),
                ('max_chars', models.IntegerField(help_text='Maximum number of characters allowed in a comment.', default=400, verbose_name='maximum characters')),
                ('club', models.OneToOneField(to='club.Club', related_name='trombi')),
            ],
        ),
        migrations.CreateModel(
            name='TrombiComment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('content', models.TextField(default='', verbose_name='content')),
            ],
        ),
        migrations.CreateModel(
            name='TrombiUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('profile_pict', models.ImageField(verbose_name='profile pict', upload_to='trombi', null=True, help_text='The profile picture you want in the trombi (warning: this picture may be published)', blank=True)),
                ('scrub_pict', models.ImageField(verbose_name='scrub pict', upload_to='trombi', null=True, help_text='The scrub picture you want in the trombi (warning: this picture may be published)', blank=True)),
                ('trombi', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='trombi', null=True, to='trombi.Trombi', blank=True, related_name='users')),
                ('user', models.OneToOneField(verbose_name='trombi user', to=settings.AUTH_USER_MODEL, related_name='trombi_user')),
            ],
        ),
        migrations.AddField(
            model_name='trombicomment',
            name='author',
            field=models.ForeignKey(verbose_name='author', to='trombi.TrombiUser', related_name='given_comments'),
        ),
        migrations.AddField(
            model_name='trombicomment',
            name='target',
            field=models.ForeignKey(verbose_name='target', to='trombi.TrombiUser', related_name='received_comments'),
        ),
    ]
