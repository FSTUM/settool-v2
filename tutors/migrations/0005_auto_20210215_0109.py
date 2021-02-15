# Generated by Django 3.1.6 on 2021-02-15 00:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutors', '0004_auto_20210130_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='mail_confirmed_place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tutors_mail_confirmed_place', to='tutors.tutormail', verbose_name='Mail Confirmed Place'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='mail_declined_place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tutors_mail_declined_place', to='tutors.tutormail', verbose_name='Mail Declined Place'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='mail_registration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tutors_mail_registration', to='tutors.tutormail', verbose_name='Mail Registration'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='mail_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tutors_mail_task', to='tutors.tutormail', verbose_name='Mail Task'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='mail_waiting_list',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tutors_mail_waiting_list', to='tutors.tutormail', verbose_name='Mail Waiting List'),
        ),
    ]
