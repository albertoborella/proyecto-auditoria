# Generated by Django 4.2 on 2025-05-05 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0002_haccp_ref_haccp'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ref_haccp',
            old_name='prr',
            new_name='haccp_list',
        ),
        migrations.AddField(
            model_name='haccp',
            name='numero',
            field=models.CharField(default=0, max_length=5),
        ),
    ]
