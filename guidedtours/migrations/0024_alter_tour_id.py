# Generated by Django 4.0.3 on 2022-04-05 15:39

import uuid

import django
from django.db import migrations, models


def migrate_tour_uuid(apps, schema_editor):
    Tour = apps.get_model("guidedtours", "Tour")
    for tour in Tour.objects.all():
        tour.uuid = uuid.uuid4()
        tour.save(update_fields=["uuid"])


def migrate_tour_id_for_participant(apps, schema_editor):
    Participant = apps.get_model("guidedtours", "Participant")
    for participant in Participant.objects.all():
        participant.tour_uuid_id = participant.tour.uuid
        participant.save(update_fields=["tour_uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("guidedtours", "0023_remove_participant_time_participant_date_and_more"),
    ]

    operations = [
        # see https://stackoverflow.com/a/48235821
        # add a new uuid-field to the Tour model
        migrations.AddField(
            model_name="tour",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, blank=True, null=True),
        ),
        migrations.RunPython(migrate_tour_uuid),
        migrations.AlterField(
            model_name="tour",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, serialize=False, unique=True),
        ),
        # add different fk-fields for each participant and logentry
        migrations.AddField(
            model_name="participant",
            name="tour_uuid",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="participant_uuid",
                to="guidedtours.tour",
                to_field="uuid",
                db_constraint=False,
            ),
        ),
        migrations.AlterField(
            model_name="participant",
            name="tour",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="participant",
                to="guidedtours.tour",
                to_field="id",
            ),
        ),
        # fill new fields with valid data
        migrations.RunPython(migrate_tour_id_for_participant),
        # after filling, we can assure the db, that they are filled
        migrations.AlterField(
            model_name="participant",
            name="tour_uuid",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="participant_uuid",
                to="guidedtours.tour",
                to_field="uuid",
            ),
        ),
        # switch to the new uuid-field
        # migrations.RemoveField(model_name="participant", name="tour"),
        migrations.RenameField(model_name="participant", old_name="tour_uuid", new_name="tour"),
    ]
