# Generated by Django 5.0.3 on 2024-06-27 15:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0002_traveler_address_destination_number_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='traveler',
            old_name='address_destination',
            new_name='addr_dest',
        ),
        migrations.RenameField(
            model_name='traveler',
            old_name='address_destination_number',
            new_name='addr_dest_num',
        ),
        migrations.RenameField(
            model_name='traveler',
            old_name='address_origin',
            new_name='addr_ori',
        ),
        migrations.RenameField(
            model_name='traveler',
            old_name='address_origin_number',
            new_name='addr_ori_num',
        ),
    ]