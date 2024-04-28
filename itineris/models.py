from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class Company(AbstractUser):
    company_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=100)
    license = models.FileField(default=None)
    is_verified = models.BooleanField(default=False)


class Travel(models.Model):
    travel_id = models.AutoField(primary_key=True)
    company = models.ForeignKey("Company", on_delete=models.DO_NOTHING)
    driver = models.ForeignKey("Driver", on_delete=models.DO_NOTHING)
    vehicle = models.ForeignKey("Vehicle", on_delete=models.DO_NOTHING)
    city_origin = models.ForeignKey("City", on_delete=models.DO_NOTHING, related_name="city_origin")
    city_destination = models.ForeignKey("City", on_delete=models.DO_NOTHING, related_name="city_destination")
    datetime_departure = models.DateTimeField()
    real_datetime_arrival = models.DateTimeField(default=None, null=True, editable=True)
    estimated_datetime_arrival = models.DateTimeField()
    duration = models.DurationField(default=timedelta(hours=1))  # En microsegundos
    fee = models.IntegerField()
    seats_left = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default="Confirmado")

    def save(self, *args, **kwargs):
        # Check if the object is being created for the first time
        if not self.pk:
            # Initialize seats_left with the capacity of the linked vehicle
            self.seats_left = self.vehicle.capacity
        super().save(*args, **kwargs)


class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=30)
    email = models.EmailField()
    phone_number = models.IntegerField()

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
    travel = models.ForeignKey("Travel", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dni = models.CharField(max_length=8)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address_origin = models.CharField(max_length=50)
    address_destination = models.CharField(max_length=50)
    feedback = models.TextField(max_length=200, null=True)
    status = models.CharField(max_length=50, default="En Proceso")


class Province(models.Model):
    province_id = models.AutoField(primary_key=True),
    name = models.CharField(max_length=20)
    acronym = models.CharField(max_length=4)

    def __str__(self):
        return self.name
