# Generated by Django 4.2.7 on 2024-02-07 19:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0009_alter_ranking_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ranking',
            unique_together={('tournament', 'team')},
        ),
    ]
