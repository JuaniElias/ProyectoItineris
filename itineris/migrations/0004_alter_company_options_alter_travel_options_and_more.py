# Generated by Django 5.1.1 on 2024-10-01 00:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineris', '0003_travel_cbu'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name': 'Listado de empresas', 'verbose_name_plural': 'Listado de empresas'},
        ),
        migrations.AlterModelOptions(
            name='travel',
            options={'verbose_name': 'Viaje a pagar', 'verbose_name_plural': 'Viajes a pagar'},
        ),
        migrations.AddField(
            model_name='traveler',
            name='refunded',
            field=models.BooleanField(default=False, verbose_name='Devolución'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address',
            field=models.CharField(max_length=100, verbose_name='Teléfono'),
        ),
        migrations.AlterField(
            model_name='company',
            name='company_name',
            field=models.CharField(max_length=100, verbose_name='Compañía'),
        ),
        migrations.AlterField(
            model_name='company',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='Verificado'),
        ),
        migrations.AlterField(
            model_name='company',
            name='license',
            field=models.FileField(upload_to='licenses', verbose_name='Licencia'),
        ),
        migrations.AlterField(
            model_name='company',
            name='phone',
            field=models.CharField(max_length=30, verbose_name='Teléfono'),
        ),
        migrations.AlterField(
            model_name='company',
            name='username',
            field=models.CharField(max_length=150, unique=True, verbose_name='CUIT'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='Compañía'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='payment_status',
            field=models.CharField(choices=[('Pendiente', 'Pendiente'), ('Pago', 'Pago')], default='Pendiente', max_length=20, verbose_name='Estado de pago'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='real_datetime_arrival',
            field=models.DateTimeField(default=None, null=True, verbose_name='Fecha de llegada'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='status',
            field=models.CharField(choices=[('Borrador', 'Borrador'), ('En Proceso', 'En Proceso'), ('Agendado', 'Agendado'), ('Finalizado', 'Finalizado'), ('Cancelado', 'Cancelado'), ('Pagado', 'Pagado')], default='Borrador', max_length=50),
        ),
        migrations.AlterField(
            model_name='travel',
            name='travel_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]