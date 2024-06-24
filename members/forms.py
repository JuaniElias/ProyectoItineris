from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from itineris.models import Company

from django import forms


class RegistrationFormCompany(UserCreationForm):
    dni_validator = RegexValidator(regex=r'^\d+$', message='El CUIT debe estar compuesto sólo por números.')

    username = forms.CharField(label='CUIT', max_length=11, validators=[dni_validator])
    company_name = forms.CharField(label='Nombre de empresa', max_length=100)
    phone = forms.CharField(label='Teléfono')
    address = forms.CharField(label='Dirección')
    license = forms.FileField(label='Licencia CNRT')

    class Meta:
        model = Company
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 'phone', 'address', 'license',)

    def __init__(self, *args, **kwargs):
        super(RegistrationFormCompany, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['company_name'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['address'].widget.attrs['class'] = 'form-control'
        self.fields['license'].widget.attrs['class'] = 'form-control'
