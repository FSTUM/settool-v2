# Generated by Django 1.9.9 on 2016-09-24 20:53

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("bags", "0011_auto_20160710_2108"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mail",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="settool_common.Semester",
            ),
        ),
    ]
