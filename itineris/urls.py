from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("work-with-us.html/", views.work_with_us, name="work-with-us"),
    path("login.html/", views.login, name="login"),
    path("sign-in.html/", views.sign_in, name="sign-in"),
    path("about-us.html/", views.about, name="about-us"),
    path("create_travel.html/", views.create_travel, name="create_travel"),
    path("pre_checkout.html/", views.pre_checkout, name="pre_checkout"),
    path("sign-in-business.html/", views.sign_in_business, name="sign-in-business"),
    path("travel_result.html/", views.travel_result, name="travel_result"),
    path("your_drivers.html/", views.your_drivers, name="your_drivers"),
    path("your_payments.html/", views.your_payments, name="your_payments"),
    path("your_vehicles.html/", views.your_vehicles, name="your_vehicles"),
]
