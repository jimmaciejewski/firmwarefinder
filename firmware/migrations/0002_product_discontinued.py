# Generated by Django 4.1.5 on 2023-01-05 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discontinued',
            field=models.BooleanField(default=False),
        ),
    ]
