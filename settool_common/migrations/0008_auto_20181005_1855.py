# Generated by Django 2.0.4 on 2018-10-05 16:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("settool_common", "0007_auto_20180705_1345"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mail",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="set_mail_set",
                to="settool_common.Semester",
            ),
        ),
    ]
