from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError

from .models import Company, Vehicle, Driver, Travel, Traveler

from django import forms
from django_select2 import forms as s2forms


def validate_positive(value):
    if value <= 0:
        raise ValidationError('Debe ingresar un numero mayor que cero')


class CompanyCreationForm(UserCreationForm):
    class Meta:
        model = Company
        fields = ('username', 'email')


class CompanyChangeForm(UserChangeForm):
    class Meta:
        model = Company
        fields = ('username', 'email')


class CityWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "city_name__icontains",
    ]


class CreateTravel(forms.ModelForm):
    city_origin = forms.CharField(label='Ciudad de origen', required=True)
    city_destination = forms.CharField(label='Ciudad de destino', required=True)
    datetime_departure = forms.DateTimeField(label='Fecha y Hora de salida', required=True,
                                             widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local',
                                                                                       'id': 'datetime_departure'}))
    estimated_datetime_arrival = forms.DateTimeField(label='Fecha y Hora de llegada', required=True,
                                                     widget=forms.widgets.DateTimeInput(
                                                         attrs={'type': 'datetime-local',
                                                                'id': 'datetime_arrival'}))
    addr_origin = forms.CharField(label='Dirección desde donde salís', required=True)
    addr_origin_num = forms.CharField(label='Número de la dirección', required=True)
    fee = forms.FloatField(label='Tarifa', required=True, validators=[validate_positive])
    driver = forms.ModelChoiceField(label='Conductor', queryset=Driver.objects.none(), required=True)
    vehicle = forms.ModelChoiceField(label='Vehículo', queryset=Vehicle.objects.none(), required=True)
    # TODO: Driver y Vehicle salen en inglés en el forms

    def clean(self):
        cleaned_data = super().clean()
        datetime_departure = cleaned_data.get('datetime_departure')
        estimated_datetime_arrival = cleaned_data.get('estimated_datetime_arrival')

        if datetime_departure and estimated_datetime_arrival:
            if datetime_departure >= estimated_datetime_arrival:
                raise forms.ValidationError('La fecha de llegada debe ser mayor que la fecha de salida.')

        return cleaned_data

    class Meta:
        model = Travel
        fields = ('city_origin', 'city_destination', 'datetime_departure', 'estimated_datetime_arrival', 'addr_origin',
                  'addr_origin_num', 'fee', 'driver', 'vehicle',)
        widgets = {
            "city_origin": CityWidget,
            "city_destination": CityWidget,
        }

    def __init__(self, company_id, *args, **kwargs):
        super(CreateTravel, self).__init__(*args, **kwargs)
        self.fields['city_origin'].widget.attrs['class'] = 'form-control'
        self.fields['city_destination'].widget.attrs['class'] = 'form-control'
        self.fields['datetime_departure'].widget.attrs['class'] = 'form-control'
        self.fields['estimated_datetime_arrival'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin_num'].widget.attrs['class'] = 'form-control'
        self.fields['fee'].widget.attrs['class'] = 'form-control'
        self.fields['driver'] = forms.ModelChoiceField(queryset=Driver.objects.filter(company_id=company_id))
        self.fields['driver'].widget.attrs['class'] = 'form-control'
        self.fields['vehicle'] = forms.ModelChoiceField(queryset=Vehicle.objects.filter(company_id=company_id,
                                                                                        status='Disponible'))
        self.fields['vehicle'].widget.attrs['class'] = 'form-control'


class CreateVehicle(forms.ModelForm):
    plate_number = forms.CharField(label='Patente', max_length=20, required=True)
    brand = forms.CharField(label='Marca', max_length=100)
    car_model = forms.CharField(label='Modelo', max_length=100)
    capacity = forms.IntegerField(label='Capacidad', validators=[validate_positive])
    color = forms.CharField(label='Color', required=False)

    class Meta:
        model = Vehicle
        fields = ('plate_number', 'brand', 'car_model', 'capacity', 'color',)

    def __init__(self, *args, **kwargs):
        super(CreateVehicle, self).__init__(*args, **kwargs)
        self.fields['plate_number'].widget.attrs['class'] = 'form-control'
        self.fields['brand'].widget.attrs['class'] = 'form-control'
        self.fields['car_model'].widget.attrs['class'] = 'form-control'
        self.fields['capacity'].widget.attrs['class'] = 'form-control'
        self.fields['color'].widget.attrs['class'] = 'form-control'


class CreateDriver(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', max_length=100, required=True)
    last_name = forms.CharField(label='Apellido', max_length=100, required=True)
    license_number = forms.CharField(label='Número de licencia', max_length=100, required=True)
    email = forms.EmailField(label='Email', max_length=100)
    phone_number = forms.CharField(label='Teléfono', max_length=100)

    class Meta:
        model = Driver
        fields = ('first_name', 'last_name', 'license_number', 'email', 'phone_number',)

    def __init__(self, *args, **kwargs):
        super(CreateDriver, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['license_number'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone_number'].widget.attrs['class'] = 'form-control'


class SearchTravel(forms.ModelForm):
    datetime_departure = forms.DateTimeField(label='Fecha Salida', required=True
                                             , widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    passengers = forms.IntegerField(label='Pasajeros', min_value=1)

    class Meta:
        model = Travel
        fields = ('city_origin', 'city_destination', 'datetime_departure', 'passengers')
        widgets = {
            "city_origin": CityWidget,
            "city_destination": CityWidget,
        }

    def __init__(self, *args, **kwargs):
        super(SearchTravel, self).__init__(*args, **kwargs)
        self.fields['datetime_departure'].widget.attrs['class'] = 'form-control'
        self.fields['passengers'].widget.attrs['class'] = 'form-control'


class PreCheckout(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', max_length=50, required=True)
    last_name = forms.CharField(label='Apellido', max_length=50, required=True)
    dni = forms.CharField(label='DNI', max_length=8, required=True)
    email = forms.EmailField(label='Email', max_length=100, required=True)
    phone = forms.CharField(label='Teléfono', max_length=30, required=True)
    addr_ori = forms.CharField(label='Dirección origen', max_length=50, required=True)
    addr_ori_num = forms.CharField(label='Número dirección origen', max_length=50, required=True)
    addr_dest = forms.CharField(label='Dirección destino', max_length=50, required=True)
    addr_dest_num = forms.CharField(label='Número dirección destino', max_length=5, required=True)

    class Meta:
        model = Traveler
        fields = ('first_name', 'last_name', 'dni', 'email', 'phone', 'addr_ori', 'addr_ori_num'
                  , 'addr_dest', 'addr_dest_num')

    def __init__(self, *args, **kwargs):
        super(PreCheckout, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['dni'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori_num'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest_num'].widget.attrs['class'] = 'form-control'
