# Generated by Django 4.1.5 on 2023-01-23 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0004_rename_subscribedusers_subscribeduser'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribeduser',
            name='send_no_updates_found',
            field=models.BooleanField(default=False),
        ),
    ]
