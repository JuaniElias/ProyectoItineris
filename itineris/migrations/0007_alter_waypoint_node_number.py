# Generated by Django 5.0.3 on 2024-08-20 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0006_remove_travel_city_destination_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waypoint',
            name='node_number',
            field=models.IntegerField(null=True),
        ),
    ]