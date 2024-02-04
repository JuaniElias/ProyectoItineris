from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    dni = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    address_origin = models.CharField(max_length=50)
    address_destination = models.CharField(max_length=50)
    feedback = models.TextField(max_length=200)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLIENT = "CLIENT", "Client"
        COMPANY = "COMPANY", "Company"

    base_role = Role.ADMIN

    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=100)
    role = models.CharField(choices=Role.choices, max_length=50)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            return super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class ClientManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=CustomUser.Role.CLIENT)


class Client(CustomUser):
    base_role = CustomUser.Role.CLIENT

    client = ClientManager()

    class Meta:
        proxy = True


@receiver(post_save, sender=Client)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "CLIENT":
        ClientProfile.objects.create(user=instance)


class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    client_id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.user.first_name


class CompanyManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=CustomUser.Role.COMPANY)


class Company(CustomUser):
    base_role = CustomUser.Role.COMPANY

    company = CompanyManager()

    class Meta:
        proxy = True


@receiver(post_save, sender=Company)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "COMPANY":
        CompanyProfile.objects.create(user=instance)


class CompanyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    license = models.FileField(default='')


class Province(models.Model):
    province_id = models.AutoField(primary_key=True),
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name
