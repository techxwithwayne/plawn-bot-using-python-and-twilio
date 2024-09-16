# Generated by Django 3.2.25 on 2024-09-12 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_alter_usersession_current_step'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersession',
            name='current_step',
        ),
        migrations.AddField(
            model_name='usersession',
            name='whatsapp_username',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('step', models.CharField(default='0', max_length=15)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='bot.usersession')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryOrders',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.TextField()),
                ('part_name', models.TextField()),
                ('vehicle_make', models.TextField()),
                ('vehicle_model', models.TextField()),
                ('manufacturer_year', models.TextField()),
                ('delivery', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_orders', to='bot.session')),
            ],
        ),
    ]
