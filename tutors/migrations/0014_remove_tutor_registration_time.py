# Generated by Django 4.0.3 on 2022-04-05 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tutors", "0013_migrate_meeting_point_to_locaton"),
    ]

    operations = [
        migrations.RemoveField(model_name="tutor", name="registration_time"),
    ]