# Generated by Django 4.2.7 on 2024-02-15 18:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0012_sport_alter_ranking_tournament_team_sport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ['sport', 'organization', 'name']},
        ),
        migrations.AddField(
            model_name='competition',
            name='sport',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.sport'),
        ),
    ]
