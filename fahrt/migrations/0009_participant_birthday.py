# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-09 19:14
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('fahrt', '0008_auto_20160906_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='birthday',
            field=models.DateField(default=datetime.datetime(2016, 9, 9, 19, 14, 35, 832001, tzinfo=utc), verbose_name='Birthday'),
            preserve_default=False,
        ),
    ]