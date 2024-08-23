# Generated by Django 5.0.3 on 2024-08-23 21:32

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nationality',
            fields=[
                ('country_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('iso_code', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('period_id', models.AutoField(primary_key=True, serialize=False)),
                ('end_date', models.DateField(default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('acronym', models.CharField(max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='Weekday',
            fields=[
                ('weekday_id', models.AutoField(primary_key=True, serialize=False)),
                ('weekday', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('company_name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=30)),
                ('address', models.CharField(max_length=100)),
                ('license', models.FileField(upload_to='licenses')),
                ('is_verified', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('driver_id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('license_number', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=30)),
                ('active', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('city_id', models.AutoField(primary_key=True, serialize=False)),
                ('city_name', models.CharField(max_length=50)),
                ('province', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='itineris.province')),
            ],
            options={
                'verbose_name_plural': 'cities',
            },
        ),
        migrations.CreateModel(
            name='Travel',
            fields=[
                ('travel_id', models.AutoField(primary_key=True, serialize=False)),
                ('addr_origin', models.CharField(max_length=100)),
                ('addr_origin_num', models.CharField(max_length=10)),
                ('url', models.CharField(default=None, max_length=5000, null=True)),
                ('payment_status', models.CharField(default='Pendiente', max_length=20)),
                ('status', models.CharField(default='Borrador', max_length=50)),
                ('real_datetime_arrival', models.DateTimeField(default=None, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.driver')),
                ('period', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.period')),
            ],
        ),
        migrations.CreateModel(
            name='Segment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DurationField()),
                ('fee', models.IntegerField(default=0, null=True)),
                ('seats_occupied', models.IntegerField(default=0)),
                ('travel', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.travel')),
            ],
        ),
        migrations.CreateModel(
            name='Traveler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('dni_type', models.CharField(max_length=9)),
                ('dni_description', models.CharField(default=None, max_length=9, null=True)),
                ('dni', models.CharField(max_length=8)),
                ('email', models.EmailField(max_length=254)),
                ('sex', models.CharField(max_length=1)),
                ('date_of_birth', models.DateField()),
                ('minor', models.BooleanField()),
                ('phone', models.CharField(max_length=30)),
                ('addr_ori', models.CharField(max_length=100)),
                ('addr_ori_num', models.CharField(max_length=10)),
                ('addr_dest', models.CharField(max_length=100)),
                ('addr_dest_num', models.CharField(max_length=10)),
                ('feedback', models.TextField(default='-', max_length=200, null=True)),
                ('payment_status', models.CharField(default='En Proceso', max_length=50)),
                ('nationality', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.nationality')),
                ('segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='itineris.segment')),
            ],
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('plate_number', models.CharField(max_length=10, primary_key=True, serialize=False, unique=True)),
                ('brand', models.CharField(max_length=20)),
                ('car_model', models.CharField(max_length=20)),
                ('capacity', models.IntegerField()),
                ('color', models.CharField(max_length=20)),
                ('status', models.CharField(default='Disponible', max_length=20)),
                ('active', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='travel',
            name='vehicle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.vehicle'),
        ),
        migrations.CreateModel(
            name='Waypoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estimated_datetime_arrival', models.DateTimeField()),
                ('node_number', models.IntegerField(null=True)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.city')),
                ('travel', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='itineris.travel')),
            ],
        ),
        migrations.AddField(
            model_name='segment',
            name='waypoint_destination',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='waypoint_destination', to='itineris.waypoint'),
        ),
        migrations.AddField(
            model_name='segment',
            name='waypoint_origin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='waypoint_origin', to='itineris.waypoint'),
        ),
        migrations.AddField(
            model_name='period',
            name='weekdays',
            field=models.ManyToManyField(related_name='weekdays', to='itineris.weekday'),
        ),
    ]
