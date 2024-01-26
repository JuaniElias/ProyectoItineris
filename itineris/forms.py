from django import forms


# Form de ejemplo
class InputForm(forms.Form):
    first_name = forms.CharField(max_length=200)
    last_name = forms.CharField(max_length=200)
    password = forms.CharField(widget=forms.PasswordInput())

# TODO: Crear forms acá para poder visualizar a la hora de hacer el sign in o log in
