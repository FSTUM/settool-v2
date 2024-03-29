# Generated by Django 2.0.4 on 2018-07-05 11:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settool_common", "0006_mail"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mail",
            name="sender",
            field=models.CharField(
                choices=[
                    ("SET-Team <set@fs.tum.de>", "SET"),
                    ("SET-Fahrt-Team <setfahrt@fs.tum.de>", "SET_FAHRT"),
                    ("SET-Tutor-Team <set-tutoren@fs.tum.de>", "SET_TUTOR"),
                ],
                default="SET-Team <set@fs.tum.de>",
                max_length=100,
                verbose_name="From",
            ),
        ),
    ]
