# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-21 08:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('settool_common', '0005_auto_20160921_1042'),
        ('guidedtours', '0007_auto_20160321_1147'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='Email subject')),
                ('text', models.TextField(help_text="You may use {{vorname}} for the participant's first name.", verbose_name='Text')),
                ('comment', models.CharField(blank=True, max_length=200, verbose_name='Comment')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tours_mail_set', to='settool_common.Semester')),
            ],
        ),
    ]