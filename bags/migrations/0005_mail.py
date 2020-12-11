# Generated by Django 1.9 on 2016-05-31 11:18

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("bags", "0004_auto_20160531_1312"),
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
                        verbose_name="Subject",
                    ),
                ),
                (
                    "text",
                    models.TextField(
                        verbose_name="Text",
                    ),
                ),
            ],
        ),
    ]
