# Generated by Django 4.1.5 on 2023-02-07 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0002_alter_product_associated_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribeduser',
            name='activated',
            field=models.BooleanField(default=False),
        ),
    ]
