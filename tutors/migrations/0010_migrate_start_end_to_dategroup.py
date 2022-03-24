# Generated by Django 4.0.3 on 2022-03-23 00:35
from math import ceil

from django.db import migrations


def migrate_start_end_to_dategroup(apps, _):
    Date = apps.get_model("kalendar", "date")

    Task = apps.get_model("tutors", "task")
    Event = apps.get_model("tutors", "event")
    for instance in list(Event.objects.all()) + list(Task.objects.all()):
        date_group = instance.associated_meetings
        start = instance.begin
        end = instance.end
        time_length = ceil((end - start).seconds / 60)
        Date.objects.create(group=date_group, date=start, probable_length=time_length)


class Migration(migrations.Migration):
    dependencies = [
        ("kalendar", "0001_initial"),
        ("tutors", "0009_add_associated_meetings_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_start_end_to_dategroup),
        migrations.RemoveField(model_name="event", name="begin"),
        migrations.RemoveField(model_name="event", name="end"),
        migrations.RemoveField(model_name="task", name="begin"),
        migrations.RemoveField(model_name="task", name="end"),
    ]
