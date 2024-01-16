from django.db import models


# Create your models here.
class Travel(models.Model):
    travel_id = models.AutoField(primary_key=True)
    company_id = models.ForeignKey("Company", on_delete=models.CASCADE)
    driver_id = models.ForeignKey("Driver", on_delete=models.CASCADE)
    plate_number = models.ForeignKey("Vehicle", on_delete=models.CASCADE)
    city_origin = models.CharField(max_length=20)
    city_destination = models.CharField(max_length=20)
    datetime_departure = models.DateTimeField()
    real_datetime_arrival = models.DateTimeField(default=None, null=True, editable=True)
    estimated_datetime_arrival = models.DateTimeField()
    distance = models.FloatField()
    fee = models.FloatField()


class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    company_id = models.ForeignKey("Company", on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    license_number = models.IntegerField()
    email = models.EmailField()
    phone_number = models.IntegerField()


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=10, unique=True, primary_key=True)
    company_id = models.ForeignKey("Company", on_delete=models.CASCADE)
    brand = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    capacity = models.IntegerField()
    color = models.CharField(max_length=20)
    status = models.CharField(max_length=20)


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    country = models.CharField(max_length=20)
    province = models.CharField(max_length=20)
    department = models.CharField(max_length=20)
    city_name = models.CharField(max_length=20)
    latitude = models.FloatField()
    longitude = models.FloatField()


# Esta es una relación, cómo se haría?
class Traveler(models.Model):
    travel_id = models.ForeignKey("Travel", on_delete=models.CASCADE)
    user_id = models.ForeignKey("User", on_delete=models.CASCADE)
    address_origin = models.CharField(max_length=50)
    address_destination = models.CharField(max_length=50)
    feedback = models.TextField(max_length=200)


class User(models.Model):
    user_id = models.IntegerField()
    username = models.CharField(max_length=15)
    password = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.IntegerField()
    address = models.CharField(max_length=50)
    city = models.ForeignKey("City", on_delete=models.CASCADE)
    name = models.CharField(max_length=20)


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
