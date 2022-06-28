# Generated by Django 4.0.3 on 2022-04-04 19:44

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fahrt", "0033_logentry_participant_uuid_and_more"),
    ]

    operations = [
        # temporarily drop the fk constraint to allow for uuid->id migration
        migrations.RunSQL(
            "ALTER TABLE fahrt_logentry DROP CONSTRAINT fahrt_logentry_participant_id_d4f3998f_fk_fahrt_par;",
        ),
        migrations.RunSQL(
            "ALTER TABLE fahrt_transportationcomment "
            "DROP CONSTRAINT fahrt_transportation_sender_id_45b9c2e3_fk_fahrt_par;",
        ),
        migrations.RunSQL(
            "ALTER TABLE fahrt_transportation DROP CONSTRAINT fahrt_transportation_creator_id_11176fde_fk_fahrt_par;",
        ),
        # uuid->id
        migrations.RemoveField(
            model_name="participant",
            name="id",
        ),
        migrations.AlterField(
            model_name="participant",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
        migrations.RenameField(
            model_name="participant",
            old_name="uuid",
            new_name="id",
        ),
        # cleanup
        migrations.AlterField(
            model_name="transportationcomment",
            name="sender",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="fahrt.participant"),
        ),
        migrations.AlterField(
            model_name="logentry",
            name="participant",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="fahrt.participant"),
        ),
        migrations.AlterField(
            model_name="transportation",
            name="creator",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="fahrt_transportation_creator",
                to="fahrt.participant",
            ),
        ),
        # re-enable the fk constraint, but to a different field
        migrations.RunSQL(
            "ALTER TABLE fahrt_logentry ADD CONSTRAINT fahrt_logentry_participant_id_d4f3998f_fk_fahrt_par "
            "FOREIGN KEY (participant_id) REFERENCES fahrt_participant (id) deferrable initially deferred;",
        ),
        migrations.RunSQL(
            "ALTER TABLE fahrt_transportationcomment ADD CONSTRAINT "
            "fahrt_transportation_sender_id_45b9c2e3_fk_fahrt_par "
            "FOREIGN KEY (sender_id) REFERENCES fahrt_participant (id) deferrable initially deferred;",
        ),
        migrations.RunSQL(
            "ALTER TABLE fahrt_transportation ADD CONSTRAINT fahrt_transportation_creator_id_11176fde_fk_fahrt_par "
            "FOREIGN KEY (creator_id) REFERENCES fahrt_participant (id) deferrable initially deferred;",
        ),
    ]
