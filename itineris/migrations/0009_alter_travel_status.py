# Generated by Django 5.0.3 on 2024-04-29 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0008_rename_model_vehicle_car_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='travel',
            name='status',
            field=models.CharField(default='Agendado', max_length=50),
        ),
    ]
