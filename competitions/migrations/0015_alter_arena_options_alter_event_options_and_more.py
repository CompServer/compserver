# Generated by Django 4.2.7 on 2024-05-03 19:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0014_merge_20240430_1925'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='arena',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['sport', 'name', 'owner']},
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='sport',
            options={'ordering': ['name']},
        ),
        migrations.AlterUniqueTogether(
            name='competition',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='arena',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='arenas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='competition',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='competitions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organization',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='organizations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='use_demo_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sport',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='sports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='team',
            name='owner',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='teams', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='arena',
            unique_together={('name', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='competition',
            unique_together={('start_date', 'name', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='organization',
            unique_together={('name', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='sport',
            unique_together={('name', 'owner')},
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('organization', 'name', 'owner')},
        ),
    ]
