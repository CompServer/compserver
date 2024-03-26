# Generated by Django 4.2.7 on 2024-03-26 19:06

import competitions.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0017_merge_20240325_1906'),
    ]

    operations = [
        migrations.RenameField(
            model_name='roundrobintournament',
            old_name='round',
            new_name='round_num',
        ),
        migrations.AlterField(
            model_name='arena',
            name='color',
            field=competitions.models.ColorField(default='#CBCBCB', image_field=None, max_length=25, samples=None),
        ),
    ]
