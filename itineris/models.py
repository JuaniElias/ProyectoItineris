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
    license_number = models.CharField(max_length=20)
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
    city_name = models.CharField(max_length=50)
    province = models.ForeignKey("Province", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "cities"

    def __str__(self):
        return self.city_name


# Esta es una relación, cómo se haría?
class Traveler(models.Model):
    travel_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey("User", on_delete=models.CASCADE)
    address_origin = models.CharField(max_length=50)
    address_destination = models.CharField(max_length=50)
    feedback = models.TextField(max_length=200)


class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=8, unique=True)
    username = models.CharField(max_length=15)
    password = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=50)
    city = models.ForeignKey("City", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    def __str__(self):
        return self.username


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=30, default='')
    address = models.CharField(max_length=50, default='')
    license = models.FileField(default='')


class Province(models.Model):
    province_id = models.AutoField(primary_key=True),
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name
