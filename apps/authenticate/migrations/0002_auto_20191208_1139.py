# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-08 11:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authenticate', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useroauthtoken',
            name='refresh_token',
            field=models.CharField(help_text=b'Refresh Token of the user used when Access Token expiers', max_length=255),
        ),
    ]