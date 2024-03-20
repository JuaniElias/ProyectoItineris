from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError

from .models import CustomUser, Vehicle, Driver, Travel, City

from django import forms


def validate_positive(value):
    if value <= 0:
        raise ValidationError('Debe ingresar un numero mayor que cero')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class AddTravel(forms.ModelForm):
    city_origin = forms.ModelChoiceField(label='Origen', queryset=City.objects.all(), empty_label="", required=True)
    city_destination = forms.ModelChoiceField(label='Destino', queryset=City.objects.all(), empty_label="", required=True)

    datetime_departure = forms.DateTimeField(label='Fecha y Hora de salida', required=True
                                             , widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}))
    estimated_datetime_arrival = forms.DateTimeField(label='Fecha y Hora de llegada', required=True,
                                                     widget=forms.widgets.DateTimeInput(
                                                         attrs={'type': 'datetime-local'}))
    fee = forms.FloatField(label='Tarifa', required=True, validators=[validate_positive])
    driver = forms.ModelChoiceField(label='Conductor', queryset=Driver.objects.none(), required=True)
    vehicle = forms.ModelChoiceField(label='Vehículo', queryset=Vehicle.objects.none(), required=True)

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
        fields = ('city_origin', 'city_destination', 'datetime_departure', 'estimated_datetime_arrival', 'fee',
                  'driver', 'vehicle',)

    def __init__(self, company_id, *args, **kwargs):
        super(AddTravel, self).__init__(*args, **kwargs)
        self.fields['city_origin'].widget.attrs['class'] = 'form-control'
        self.fields['city_destination'].widget.attrs['class'] = 'form-control'
        self.fields['datetime_departure'].widget.attrs['class'] = 'form-control'
        self.fields['estimated_datetime_arrival'].widget.attrs['class'] = 'form-control'
        self.fields['fee'].widget.attrs['class'] = 'form-control'
        self.fields['driver'] = forms.ModelChoiceField(queryset=Driver.objects.filter(company_id=company_id))
        self.fields['driver'].widget.attrs['class'] = 'form-control'
        self.fields['vehicle'] = forms.ModelChoiceField(queryset=Vehicle.objects.filter(company_id=company_id))
        self.fields['vehicle'].widget.attrs['class'] = 'form-control'


class AddVehicle(forms.ModelForm):
    plate_number = forms.CharField(label='Patente', max_length=20, required=True)
    brand = forms.CharField(label='Marca', max_length=100)
    model = forms.CharField(label='Modelo', max_length=100)
    capacity = forms.IntegerField(label='Capacidad', validators=[validate_positive])
    color = forms.CharField(label='Color', required=False)

    class Meta:
        model = Vehicle
        fields = ('plate_number', 'brand', 'model', 'capacity', 'color',)

    def __init__(self, *args, **kwargs):
        super(AddVehicle, self).__init__(*args, **kwargs)
        self.fields['plate_number'].widget.attrs['class'] = 'form-control'
        self.fields['brand'].widget.attrs['class'] = 'form-control'
        self.fields['model'].widget.attrs['class'] = 'form-control'
        self.fields['capacity'].widget.attrs['class'] = 'form-control'
        self.fields['color'].widget.attrs['class'] = 'form-control'


class AddDriver(forms.ModelForm):
    name = forms.CharField(label='Nombre y apellido', max_length=100, required=True)
    license_number = forms.CharField(label='Número de licencia', max_length=100, required=True)
    email = forms.EmailField(label='Email', max_length=100)
    phone_number = forms.CharField(label='Teléfono', max_length=100)

    class Meta:
        model = Driver
        fields = ('name', 'license_number', 'email', 'phone_number',)

    def __init__(self, *args, **kwargs):
        super(AddDriver, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['license_number'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone_number'].widget.attrs['class'] = 'form-control'
