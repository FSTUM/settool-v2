# Generated by Django 3.1.7 on 2021-03-17 10:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settool_common", "0013_anonymisationlog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="qrcode",
            name="content",
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
