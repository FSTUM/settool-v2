# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-31 11:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bags', '0005_mail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='subject',
            field=models.CharField(max_length=200, verbose_name='Email subject'),
        ),
    ]
