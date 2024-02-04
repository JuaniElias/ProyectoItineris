from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from itineris.models import Client, Company

from django import forms


class RegistrationForm(UserCreationForm):
    # Valida que el DNI sean solo numeros
    dni_validator = RegexValidator(regex=r'^\d+$', message='El DNI debe estar compuesto solo por numeros.')

    username = forms.CharField(label='DNI', max_length=8, validators=[dni_validator])
    first_name = forms.CharField(label='Nombre')
    last_name = forms.CharField(label='Apellido')
    phone = forms.CharField(label='Telefono')

    class Meta:
        model = Client
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class RegistrationFormCompany(UserCreationForm):

    username = forms.CharField(label='Nombre de la empresa', max_length=100)
    phone = forms.CharField(label='Teléfono')

    class Meta:
        model = Company
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegistrationFormCompany, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
