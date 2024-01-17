from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("work-with-us.html/", views.work_with_us, name="work-with-us"),
    path("login.html/", views.login, name="login"),
    path("sign-in.html/", views.sign_in, name="sign-in")
]