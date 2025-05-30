# Generated by Django 4.2 on 2025-05-07 19:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0004_alter_haccp_numero_alter_haccp_principio'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoConformidades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=10)),
                ('seccion', models.TextField(blank=True, max_length=255, null=True)),
                ('nc', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ref_noconformidades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.CharField(max_length=255)),
                ('nc_lista', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ref_noconformidades', to='questions.noconformidades')),
            ],
        ),
    ]
