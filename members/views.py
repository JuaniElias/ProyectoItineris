from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from members.forms import RegistrationFormCompany
from utils.utils import send_email


def login_user(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('your_travels')
        else:
            messages.success(request, 'Hubo un error al iniciar el usuario, intente otra vez.')
            return redirect('login')

    else:
        return render(request, 'authenticate/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'Se ha cerrado su  sesión.')
    return redirect('index')


def sign_up_business(request):
    if request.method == "POST":
        form = RegistrationFormCompany(request.POST, request.FILES)
        if form.is_valid():
            # Se envia un mail a los admin para notificar que se creo una nueva Company para validar su licencia DNRPA
            to_email = settings.EMAIL_HOST_USER
            subject = 'Nueva empresa requiere verificación'
            message = (f'La empresa {form.cleaned_data["company_name"]} quiere registrarse en Itineris\n'
                       f'Información de Contacto\n'
                       f'Email: {form.cleaned_data["email"]}\n'
                       f'Teléfono: {form.cleaned_data["phone"]}\n')
            file = request.FILES.get('license')

            try:
                send_email(to_email, subject, message, file)
                messages.success(request,
                                 'Email enviado correctamente.')
            except Exception as e:
                messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')

            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('your_travels')
    else:
        form = RegistrationFormCompany()

    return render(request, 'authenticate/sign_up_business.html', {
        'form': form,
    })
