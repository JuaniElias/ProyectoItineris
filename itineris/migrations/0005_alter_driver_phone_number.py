# Generated by Django 5.0.3 on 2024-08-10 04:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0004_alter_traveler_dni_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='driver',
            name='phone_number',
            field=models.CharField(max_length=30),
        ),
    ]
