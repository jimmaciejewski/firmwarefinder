# Generated by Django 4.1.5 on 2023-09-27 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0010_alter_version_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='store_firmware_versions_locally',
            field=models.BooleanField(default=True),
        ),
    ]