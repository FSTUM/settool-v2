# Generated by Django 2.0.4 on 2018-10-05 16:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fahrt", "0021_auto_20180704_0855"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fahrt",
            name="semester",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="settool_common.Semester",
            ),
        ),
        migrations.AlterField(
            model_name="logentry",
            name="participant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="fahrt.Participant",
            ),
        ),
        migrations.AlterField(
            model_name="logentry",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mylogentry_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="mail",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fahrt_mail_set",
                to="settool_common.Semester",
            ),
        ),
        migrations.AlterField(
            model_name="participant",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fahrt_participant",
                to="settool_common.Semester",
            ),
        ),
        migrations.AlterField(
            model_name="participant",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fahrt_participant",
                to="settool_common.Subject",
                verbose_name="Subject",
            ),
        ),
    ]
