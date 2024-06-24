from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from members.forms import RegistrationFormCompany


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
