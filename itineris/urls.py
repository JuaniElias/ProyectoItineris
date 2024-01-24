from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("work-with-us.html/", views.work_with_us, name="work-with-us"),
    path("login.html/", views.login, name="login"),
    path("sign-up.html/", views.sign_up, name="sign-up"),
    path("about-us.html/", views.about, name="about-us"),
    path("create_travel.html/", views.create_travel, name="create_travel"),
    path("pre_checkout.html/", views.pre_checkout, name="pre_checkout"),
    path("sign-up-business.html/", views.sign_up_business, name="sign-up-business"),
    path("travel_result.html/", views.travel_result, name="travel_result"),
    path("your_drivers.html/", views.your_drivers, name="your_drivers"),
    path("your_payments.html/", views.your_payments, name="your_payments"),
    path("your_travels.html/", views.your_travels, name="your_travels"),
    path("your_vehicles.html/", views.your_vehicles, name="your_vehicles"),
    path("navbar.html/", views.navbar, name="navbar"),
]
