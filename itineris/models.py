import pandas as pd
from Scripts.pywin32_postinstall import verbose
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date

from django.db.models import Sum


# Create your models here.

class Company(AbstractUser):
    company_name = models.CharField(max_length=100, verbose_name='Compañía')
    phone = models.CharField(max_length=30, verbose_name='Teléfono')
    address = models.CharField(max_length=100, verbose_name='Teléfono')
    license = models.FileField(upload_to='licenses', verbose_name='Licencia')
    is_verified = models.BooleanField(default=False, verbose_name='Verificado')
    cbu = models.CharField(max_length=22)

    username = models.CharField(max_length=150, unique=True, verbose_name="CUIT")

    class Meta:
        verbose_name = "Listado de empresas"
        verbose_name_plural = "Listado de empresas"

    def __str__(self):
        return str(self.company_name) + ' (' + str(self.username) + ')'


class Travel(models.Model):
    STATUS_CHOICES = [
        ('Borrador', 'Borrador'),
        ('En Proceso', 'En Proceso'),
        ('Agendado', 'Agendado'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
        ('Pagado', 'Pagado'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pago', 'Pago')
    ]

    travel_id = models.AutoField(primary_key=True, verbose_name='ID')
    company = models.ForeignKey("Company", on_delete=models.DO_NOTHING, verbose_name='Compañía')
    driver = models.ForeignKey("Driver", on_delete=models.DO_NOTHING, verbose_name='Conductor')
    vehicle = models.ForeignKey("Vehicle", on_delete=models.DO_NOTHING, verbose_name='Vehiculo')
    address = models.CharField(max_length=200, null=True)
    geocode = models.CharField(max_length=100, null=True)
    url = models.CharField(max_length=5000, default=None, editable=True, null=True)
    payment_status = models.CharField(max_length=20, default="Pendiente",choices=PAYMENT_STATUS_CHOICES, verbose_name='Estado de pago')
    period = models.ForeignKey("Period", on_delete=models.DO_NOTHING, default=None, null=True, editable=True)
    status = models.CharField(max_length=50, default="Borrador", choices=STATUS_CHOICES, verbose_name='Estado del viaje')
    real_datetime_arrival = models.DateTimeField(default=None, null=True, editable=True, verbose_name='Fecha de llegada')

    class Meta:
        verbose_name = "Viaje a pagar"
        verbose_name_plural = "Viajes a pagar"

    @property
    def gross_revenue(self):
        gross_rev = (Traveler.objects.filter(segment__travel=self.travel_id,
                                             payment_status='Confirmado')
                     .aggregate(total=Sum('paid_amount'))
                     ['total'] or 0
                     )
        return gross_rev

    gross_revenue.fget.short_description = "Total a pagar"

    @property
    def origin(self):
        return self.waypoint_set.all().order_by('node_number').first()

    @property
    def destination(self):
        return self.waypoint_set.all().order_by('node_number').last()

    @property
    def payment_info(self):
        return self.company.cbu
    payment_info.fget.short_description = "CBU"

class Segment(models.Model):
    travel = models.ForeignKey("Travel", on_delete=models.DO_NOTHING)
    waypoint_origin = models.ForeignKey("Waypoint", on_delete=models.DO_NOTHING, related_name='waypoint_origin')
    waypoint_destination = models.ForeignKey("Waypoint", on_delete=models.DO_NOTHING,
                                             related_name='waypoint_destination')
    duration = models.DurationField()  # En microsegundos
    fee = models.IntegerField(default=0, null=True)
    seats_occupied = models.IntegerField(default=0)

    def __str__(self):
        return str(self.waypoint_origin.city) + ' - ' + str(self.waypoint_destination.city)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.duration = self.waypoint_destination.estimated_datetime_arrival - self.waypoint_origin.estimated_datetime_arrival
        super().save(*args, **kwargs)

    @property
    def seats_available(self):
        # Obtener todos los segmentos asociados al mismo Travel
        travel_segments = Segment.objects.filter(travel=self.travel)

        # Obtener los segmentos que coinciden en el mismo tramo entre ciudades excluyendo los segmentos en ambos extremos
        vehicle_capacity = self.travel.vehicle.capacity

        start_waypoint = self.waypoint_origin.node_number
        end_waypoint = self.waypoint_destination.node_number

        excluded_before_start = travel_segments.filter(travel_id=self.travel.travel_id,
                                                       waypoint_destination__node_number__lte=start_waypoint
                                                       )
        excluded_after_end = travel_segments.filter(travel_id=self.travel.travel_id,
                                                    waypoint_origin__node_number__gte=end_waypoint,
                                                    )

        valid_segments = travel_segments.exclude(id__in=excluded_before_start).exclude(id__in=excluded_after_end)

        total_seats = valid_segments.aggregate(total=Sum('seats_occupied'))['total'] or 0

        return vehicle_capacity - total_seats

    @property
    def revenue(self):
        travelers = self.traveler_set.filter(payment_status='Confirmado')
        revenue = travelers.aggregate(total=Sum('paid_amount'))['total'] or 0
        return revenue


class Waypoint(models.Model):
    travel = models.ForeignKey("Travel", on_delete=models.DO_NOTHING)
    city = models.ForeignKey("City", on_delete=models.DO_NOTHING)
    estimated_datetime_arrival = models.DateTimeField()
    node_number = models.IntegerField(editable=True, null=True)
    url = models.CharField(max_length=5000, default=None, editable=True, null=True)

    @property
    def seats_available(self):
        if self.node_number == 0:
            return 0
        else:
            # Se buscan todos los segmentos que terminen en el nodo o que comiencen antes del nodo y terminen después de él.
            valid_segments = Segment.objects.filter(travel=self.travel,
                                                    waypoint_origin__node_number__lt=self.node_number,
                                                    waypoint_destination__node_number__gte=self.node_number
                                                    )

            # node 2 --> (0, 2) (0, 3) (1, 2) (1, 3)
            # (0, 1) (0, 2) (0, 3)
            # (1, 2) (1, 3)
            # (2, 3)

            total_seats = valid_segments.aggregate(total=Sum('seats_occupied'))['total'] or 0

            return total_seats

    @property
    def travelers_to_pick_up(self):
        last_waypoint = Waypoint.objects.filter(travel=self.travel).order_by('node_number').last()

        if self.node_number == last_waypoint.node_number:
            return '-'
        else:
            valid_segments = Segment.objects.filter(travel=self.travel,
                                                    waypoint_origin__node_number=self.node_number,
                                                    )

            total_seats = valid_segments.aggregate(total=Sum('seats_occupied'))['total'] or 0

            return total_seats

    @property
    def travelers_to_drop_off(self):
        if self.node_number == 0:
            return '-'
        else:
            valid_segments = Segment.objects.filter(travel=self.travel,
                                                    waypoint_destination__node_number=self.node_number
                                                    )
            total_seats = valid_segments.aggregate(total=Sum('seats_occupied'))['total'] or 0

            return total_seats


class Period(models.Model):
    period_id = models.AutoField(primary_key=True)
    weekdays = models.ManyToManyField("Weekday", related_name="weekdays")
    end_date = models.DateField(default=None, null=True)


class Weekday(models.Model):
    weekday_id = models.AutoField(primary_key=True)
    weekday = models.CharField(max_length=10)

    def __str__(self):
        return self.weekday


class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=30)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name + " (" + self.license_number + ")"


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=10, unique=True, primary_key=True)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    brand = models.CharField(max_length=20)
    car_model = models.CharField(max_length=20)
    capacity = models.IntegerField()
    color = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default="Disponible")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.brand + ' ' + self.car_model + " (" + self.plate_number + ")"


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=50)
    province = models.ForeignKey("Province", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "cities"

    def __str__(self):
        return self.city_name + ' (' + self.province.acronym + ')'


class Traveler(models.Model):
    segment = models.ForeignKey("Segment", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, verbose_name='Nombre')
    last_name = models.CharField(max_length=50, verbose_name='Apellido')
    dni_type = models.CharField(max_length=9)
    dni_description = models.CharField(max_length=9, default=None, null=True)
    dni = models.CharField(max_length=8)
    email = models.EmailField()
    sex = models.CharField(max_length=1)
    date_of_birth = models.DateField()
    minor = models.BooleanField()
    nationality = models.ForeignKey("Nationality", on_delete=models.DO_NOTHING)
    phone = models.CharField(max_length=30, verbose_name='Teléfono')
    address_origin = models.CharField(max_length=200, null=True)
    geocode_origin = models.CharField(max_length=100, null=True)
    address_destination = models.CharField(max_length=200, null=True)
    geocode_destination = models.CharField(max_length=100, null=True)
    feedback = models.TextField(max_length=200, null=True, default='-')
    payment_status = models.CharField(max_length=50,
                                      default="En Proceso", verbose_name='Estado de pago')  # En Proceso | Confirmado | Cancelado
    paid_amount = models.IntegerField(verbose_name='Total pagado')
    refunded = models.BooleanField(default=False, verbose_name='Devolución')

    class Meta:
        verbose_name = "Pasajero pendiente de devolución"
        verbose_name_plural = "Pasajeros pendientes de devolución"

    def save(self, *args, **kwargs):
        if not self.pk:
            age = (pd.to_datetime(date.today()) - pd.to_datetime(self.date_of_birth)) // pd.Timedelta(days=365.25)
            self.minor = True if age < 18 else False

            if self.dni_type == 'OTRO':
                self.dni_description = 'OTRO'
            else:
                self.dni_description = None

        self.paid_amount = self.segment.fee

        super().save(*args, **kwargs)

        self.update_seats_occupied()

    def update_seats_occupied(self):
        confirmed_travelers = Traveler.objects.filter(segment=self.segment, payment_status='Confirmado').count()
        self.segment.seats_occupied = confirmed_travelers
        self.segment.save()


class Province(models.Model):
    province_id = models.AutoField(primary_key=True),
    name = models.CharField(max_length=20)
    acronym = models.CharField(max_length=4)

    def __str__(self):
        return self.name


class Nationality(models.Model):
    country_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    iso_code = models.CharField(max_length=2)

    def __str__(self):
        return self.name
