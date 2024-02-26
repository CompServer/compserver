# Generated by Django 4.2.6 on 2024-02-26 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0017_alter_match_time'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='abstracttournament',
            options={'ordering': ['competition', 'points', 'event']},
        ),
        migrations.AlterField(
            model_name='abstracttournament',
            name='points',
            field=models.DecimalField(decimal_places=10, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='match',
            name='time',
            field=models.DateTimeField(),
        ),
    ]
