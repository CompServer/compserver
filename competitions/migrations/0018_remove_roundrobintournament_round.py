# Generated by Django 4.2.7 on 2024-03-26 03:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0017_merge_20240325_1906'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roundrobintournament',
            name='round',
        ),
    ]
