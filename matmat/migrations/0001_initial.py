# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0007_auto_20170324_0917'),
    ]

    operations = [
        migrations.CreateModel(
            name='Matmat',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('subscription_deadline', models.DateField(verbose_name='subscription deadline', default=django.utils.timezone.now, help_text='Before this date, users are allowed to subscribe to this Matmatronch. After this date, users subscribed will be allowed to comment on each other.')),
                ('comments_deadline', models.DateField(verbose_name='comments deadline', default=django.utils.timezone.now, help_text="After this date, users won't be able to make comments anymore")),
                ('club', models.OneToOneField(related_name='matmat', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='MatmatComment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='matmat', to=settings.AUTH_USER_MODEL, related_name='users', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MatmatUser',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('matmat', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, verbose_name='matmat', to='matmat.Matmat', related_name='users', null=True)),
                ('user', models.OneToOneField(related_name='matmat_user', verbose_name='matmat user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
