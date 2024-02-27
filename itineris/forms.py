from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, Vehicle

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
