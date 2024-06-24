from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CompanyCreationForm, CompanyChangeForm
# Register your models here.
from .models import Company, City
from django.utils.html import format_html


class CompanyAdmin(UserAdmin):
    add_form = CompanyCreationForm
    form = CompanyChangeForm
    model = Company

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('company_name', 'phone', 'address', 'license', 'is_verified')}),
    )
    list_display = ('username', 'email', 'company_name', 'phone', 'is_verified', 'view_license')
    search_fields = ('username', 'email', 'company_name', 'phone')

    def view_license(self, obj):
        if obj.license:
            return format_html('<a href="{}">Ver Licencia</a>', obj.license.url)
        return "No disponible"

    view_license.short_description = "Licencia"


admin.site.register(Company, CompanyAdmin)

admin.site.register(City)
