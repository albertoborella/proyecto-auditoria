# Generated by Django 4.2 on 2025-04-04 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0004_respuesta_observaciones_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='respuesta',
            name='texto_critico',
            field=models.BooleanField(default=False),
        ),
    ]
