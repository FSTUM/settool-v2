# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-06 12:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fahrt', '0007_auto_20160906_1441'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participant',
            options={'permissions': (('view_participants', 'Can view and edit the list of participants'),)},
        ),
    ]