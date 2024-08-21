from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class Company(AbstractUser):
    company_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=100)
    license = models.FileField(upload_to='licenses')
    is_verified = models.BooleanField(default=False)


class Travel(models.Model):
    travel_id = models.AutoField(primary_key=True)
    company = models.ForeignKey("Company", on_delete=models.DO_NOTHING)
    driver = models.ForeignKey("Driver", on_delete=models.DO_NOTHING)
    vehicle = models.ForeignKey("Vehicle", on_delete=models.DO_NOTHING)
    addr_origin = models.CharField(max_length=100)
    addr_origin_num = models.CharField(max_length=10)
    url = models.CharField(max_length=5000, default=None, editable=True, null=True)
    payment_status = models.CharField(max_length=20, default="Pendiente")  # Pendiente | Pago
    period = models.ForeignKey("Period", on_delete=models.DO_NOTHING, default=None, null=True, editable=True)
    status = models.CharField(max_length=50, default="Borrador")  # En Proceso | Agendado | Finalizado | Cancelado | Borrador
    real_datetime_arrival = models.DateTimeField(default=None, null=True, editable=True)


class Segment(models.Model):
    travel = models.ForeignKey("Travel", on_delete=models.DO_NOTHING)
    waypoint_origin = models.ForeignKey("Waypoint", on_delete=models.DO_NOTHING, related_name='waypoint_origin')
    waypoint_destination = models.ForeignKey("Waypoint", on_delete=models.DO_NOTHING,
                                             related_name='waypoint_destination')
    duration = models.DurationField()  # En microsegundos
    fee = models.IntegerField(default=0, null=True)
    seats_occupied = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.duration = self.waypoint_destination.estimated_datetime_arrival - self.waypoint_origin.estimated_datetime_arrival
        super().save(*args, **kwargs)
     # TODO:
    '''def has_space_available(self, num_seats):
        # Obtener todos los segmentos asociados al mismo Travel
        all_segments = Segment.objects.filter(travel=self.travel)

        # Obtener la capacidad total del vehículo asociado a este Travel
        vehicle_capacity = self.travel.vehicle.capacity
        
        for segment in segments_raw_queryset:
            segment_start = segment.waypoint_origin.node_number
            segment_end = segment.waypoint_destination.node_number

            s = Segment.objects.all().filter(travel_id=segment.travel.travel_id,
                                         waypoint_origin__node_number__gte=segment_start,
                                         waypoint_destination__node_number__lte=segment_end)
            if s.values('seats_occupied') > passengers:
                pass

        # Verificar si hay espacio disponible
        if total_seats_occupied + num_seats <= vehicle_capacity:
            return True
        else:
            return False'''


class Waypoint(models.Model):
    travel = models.ForeignKey("Travel", on_delete=models.DO_NOTHING)
    city = models.ForeignKey("City", on_delete=models.DO_NOTHING)
    estimated_datetime_arrival = models.DateTimeField()
    node_number = models.IntegerField(editable=True, null=True)


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
    travel = models.ForeignKey("Segment", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dni_type = models.CharField(max_length=9)
    dni_description = models.CharField(max_length=9, default=None, null=True)
    dni = models.CharField(max_length=8)
    email = models.EmailField()
    sex = models.CharField(max_length=1)
    minor = models.BooleanField()
    nationality = models.ForeignKey("Nationality", on_delete=models.DO_NOTHING)
    # TODO: Poner default a la hora de hacer la carga
    phone = models.CharField(max_length=30)
    # FIXME: Si terminamos aplicando la Places API de Google vamos a seguir guardando de esta manera las direcciones?
    #  Es decir, separar la dirección de la altura.
    addr_ori = models.CharField(max_length=100)
    addr_ori_num = models.CharField(max_length=10)
    addr_dest = models.CharField(max_length=100)
    addr_dest_num = models.CharField(max_length=10)
    feedback = models.TextField(max_length=200, null=True, default='-')
    payment_status = models.CharField(max_length=50,
                                      default="En Proceso")  # En Proceso | Confirmado | Finalizado | Cancelado


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
