# Generated by Django 5.1.7 on 2025-06-17 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_remove_rutinaasignada_completada_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rutinaasignada',
            name='detalles',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
