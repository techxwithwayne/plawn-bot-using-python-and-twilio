# Generated by Django 3.2.25 on 2024-09-12 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_auto_20240912_1036'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='status',
            field=models.CharField(default='active', max_length=10),
        ),
    ]
