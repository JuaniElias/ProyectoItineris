from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CompanyCreationForm, CompanyChangeForm
# Register your models here.
from .models import Company, City


class CompanyAdmin(UserAdmin):
    add_form = CompanyCreationForm
    form = CompanyChangeForm
    model = Company
    list_display = ["email", "username"]


admin.site.register(Company, CompanyAdmin)

admin.site.register(City)
