# Generated by Django 4.1.5 on 2023-05-24 01:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0009_alter_version_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2023, 5, 24, 1, 42, 51, 838873, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
