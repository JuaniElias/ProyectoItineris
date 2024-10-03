from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from .models import Company, Travel, Traveler
from django.utils.html import format_html

class CompanyAdmin(UserAdmin):
    list_display = ('username', 'company_name', 'email', 'phone', 'is_verified', 'view_license')
    search_fields = ('username', 'email', 'company_name', 'phone')

    readonly_fields = ('company_name', 'password', 'phone', 'address', 'username', 'email')

    fieldsets = (
        ('Información de la Compañía', {
            'fields': ('username', 'email', 'company_name', 'phone', 'is_verified')
        }),
        ('Licencia', {
            'fields': ('license',)
        }),
    )

    def view_license(self, obj):
        if obj.license:
            return format_html('<a href="{}">Ver Licencia</a>', obj.license.url)
        return "No disponible"

    view_license.short_description = "Licencia"

admin.site.register(Company, CompanyAdmin)

class TravelAdmin(admin.ModelAdmin):
    list_display = ('travel_id', 'company', 'payment_status', 'status', 'real_datetime_arrival', 'payment_info', 'gross_revenue')
    list_filter = ('company', 'payment_status', 'status')

    readonly_fields = ('travel_id', 'company', 'driver', 'vehicle', 'address', 'geocode', 'status'
                       , 'real_datetime_arrival' ,'gross_revenue', 'url', 'period')

    fieldsets = (
        ('Información del viaje', {
            'fields': ('travel_id', 'company', 'status',)
        }),
        ('Información de pagos', {
            'fields': ('payment_status',)
        }),
    )

    def get_queryset(self, request):
        # Filtrar los viajes que están pendientes de pago y finalizados
        queryset = super().get_queryset(request)
        return queryset.filter(payment_status='Pendiente', status='Finalizado')

admin.site.register(Travel, TravelAdmin)

class TravelerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'dni', 'email', 'phone', 'payment_status', 'paid_amount', 'refunded')

    readonly_fields = ('first_name', 'last_name', 'dni', 'email', 'phone', 'payment_status', 'paid_amount')

    fields = ('first_name', 'last_name', 'dni', 'email', 'phone', 'payment_status', 'paid_amount', 'refunded')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(payment_status='Cancelado', refunded=False)
admin.site.register(Traveler, TravelerAdmin)
