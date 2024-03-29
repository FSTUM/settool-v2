# Generated by Django 1.9 on 2016-09-10 10:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settool_common", "0004_auto_20151220_2255"),
        ("fahrt", "0010_fahrt"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        max_length=200,
                        verbose_name="Email subject",
                    ),
                ),
                (
                    "text",
                    models.TextField(
                        help_text="You may use {{vorname}} for the participants first name.",
                        verbose_name="Text",
                    ),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        verbose_name="Comment",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fahrt_mail_set",
                        to="settool_common.Semester",
                    ),
                ),
            ],
        ),
    ]
