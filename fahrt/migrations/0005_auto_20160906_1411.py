# Generated by Django 1.9 on 2016-09-06 12:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("fahrt", "0004_auto_20160906_1409"),
    ]

    operations = [
        migrations.RenameField(
            model_name="person",
            old_name="time",
            new_name="registration_time",
        ),
    ]
