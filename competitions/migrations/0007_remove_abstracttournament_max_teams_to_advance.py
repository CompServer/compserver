# Generated by Django 4.2.7 on 2024-06-01 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0006_abstracttournament_max_teams_to_advance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='abstracttournament',
            name='max_teams_to_advance',
        ),
    ]
