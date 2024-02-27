from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from members.forms import RegistrationForm, RegistrationFormCompany, BusinessDetails
from itineris.models import CompanyProfile, CustomUser


def login_user(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'COMPANY':
                return redirect('your_travels')
            return redirect('index')
        else:
            messages.success(request, 'Hubo un error al iniciar el usuario, intente otra vez.')
            return redirect('login')

    else:
        return render(request, 'authenticate/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'Se ha cerrado su  sesión.')
    return redirect('index')


def sign_up_user(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "Se ha registrado correctamente.")
            return redirect('index')
    else:
        form = RegistrationForm()

    return render(request, 'authenticate/sign-up.html', {
        'form': form,
    })


def sign_up_business(request):
    if request.method == "POST":
        form = RegistrationFormCompany(request.POST)
        if form.is_valid():
            user = form.save()
            request.session['user_id'] = user.id
            return redirect('finish-sign-up-business')
    else:
        form = RegistrationFormCompany()

    return render(request, 'authenticate/sign-up-business.html', {
        'form': form,
    })


def finish_sign_up_business(request):
    if 'user_id' not in request.session:
        return redirect('sign-up-business')

    user_id = request.session.get('user_id')
    user = get_object_or_404(CompanyProfile, user_id=user_id)
    custom_user = get_object_or_404(CustomUser, pk=user_id)

    if request.method == "POST":
        form = BusinessDetails(request.POST, instance=user)
        if form.is_valid():
            form.save()
            login(request, custom_user)
            return redirect('your_travels')
    else:
        form = BusinessDetails(instance=user)

    return render(request, 'authenticate/finish-sign-up-business.html', {
        'form': form,
    })
