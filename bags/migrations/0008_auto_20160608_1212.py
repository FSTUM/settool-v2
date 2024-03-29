# Generated by Django 1.9 on 2016-06-08 10:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bags", "0007_auto_20160601_0949"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="company",
            name="contact",
        ),
        migrations.AddField(
            model_name="company",
            name="contact_firstname",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="Contact person (First Name)",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="contact_gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("m", "Herr"),
                    ("w", "Frau"),
                ],
                max_length=200,
                verbose_name="Contact person (Gender)",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="contact_lastname",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="Contact person (Last Name)",
            ),
        ),
    ]
