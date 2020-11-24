# Generated by Django 2.0.4 on 2018-10-05 16:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guidedtours', '0011_auto_20180704_0855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tours_mail_set', to='settool_common.Semester'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='settool_common.Subject', verbose_name='Subject'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='tour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='guidedtours.Tour', verbose_name='Tour'),
        ),
        migrations.AlterField(
            model_name='tour',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='settool_common.Semester'),
        ),
    ]
