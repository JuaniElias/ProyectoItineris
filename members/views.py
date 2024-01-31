from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_user(request):
    if request.method == 'POST':
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('')
        else:
            messages.success(request, 'Hubo un error al iniciar el usuario, intente otra vez')
            return redirect('login')

    else:
        return render(request, 'authenticate/login.html')
