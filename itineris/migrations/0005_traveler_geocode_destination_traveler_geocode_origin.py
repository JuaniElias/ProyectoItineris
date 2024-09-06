# Generated by Django 5.0.3 on 2024-09-06 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0004_remove_traveler_addr_dest_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='traveler',
            name='geocode_destination',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='traveler',
            name='geocode_origin',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
