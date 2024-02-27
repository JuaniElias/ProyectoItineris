from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, Vehicle, Driver

from django import forms


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class AddVehicle(forms.ModelForm):

    plate_number = forms.CharField(label='Patente', max_length=20, required=True)
    brand = forms.CharField(label='Marca', max_length=100)
    model = forms.CharField(label='Modelo', max_length=100)
    capacity = forms.IntegerField(label='Capacidad')
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
