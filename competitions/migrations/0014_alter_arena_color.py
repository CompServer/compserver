# Generated by Django 4.2.7 on 2024-03-22 02:25

#import colorfield.fields
from ..models import ColorField
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0013_alter_arena_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arena',
            name='color',
            field=ColorField(default='#CBCBCB', image_field=None, max_length=25, samples=None),
        ),
    ]
