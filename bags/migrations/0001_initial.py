# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-27 07:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('settool_common', '0004_auto_20151220_2255'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('contact', models.CharField(max_length=200, verbose_name='Contact person')),
                ('email', models.CharField(max_length=200, verbose_name='Email address')),
                ('email_sent', models.BooleanField(verbose_name='Email sent')),
                ('email_sent_success', models.BooleanField(verbose_name='Email successfully sent')),
                ('zusage', models.NullBooleanField(verbose_name='Zusage')),
                ('giveaways', models.CharField(max_length=200, verbose_name='Giveaways')),
                ('arrival_time', models.CharField(max_length=200, verbose_name='Arrival time')),
                ('comment', models.CharField(max_length=200, verbose_name='Comment')),
                ('last_year', models.BooleanField(verbose_name='Participated last year')),
                ('arrived', models.BooleanField(verbose_name='Arrived')),
                ('contact_again', models.NullBooleanField(verbose_name='Contact again')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='settool_common.Semester')),
            ],
        ),
    ]
