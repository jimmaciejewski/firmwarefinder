# Generated by Django 4.1.5 on 2023-01-09 05:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firmware', '0003_subscribedusers'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SubscribedUsers',
            new_name='SubscribedUser',
        ),
    ]
