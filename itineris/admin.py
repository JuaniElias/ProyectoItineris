from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
# Register your models here.
from .models import CustomUser, City, ClientProfile, CompanyProfile


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "username", "role",]


admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(City)
