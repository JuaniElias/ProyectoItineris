from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("select2/", include("django_select2.urls")),
    path("work-with-us", views.work_with_us, name="work-with-us"),
    path("about-us", views.about, name="about-us"),
    path("create_travel", views.create_travel, name="create_travel"),
    path("get_available_options", views.get_available_options, name="get_available_options"),
    path("pre_checkout", views.pre_checkout, name="pre_checkout"),  # TODO: Redundante?
    path("pre_checkout/<str:travel_id>/<str:passengers>", views.pre_checkout, name="pre_checkout"),
    path("travel_result", views.travel_result, name="travel_result"),
    path("your_drivers", views.your_drivers, name="your_drivers"),
    path('delete_driver/<str:driver_id>/', views.delete_driver, name='delete_driver'),
    path("your_payments", views.your_payments, name="your_payments"),
    path("your_travels", views.your_travels, name="your_travels"),
    path("travel_detail/<str:travel_id>/", views.travel_detail, name="travel_detail"),
    path('delete_travel/<str:travel_id>/', views.delete_travel, name='delete_travel'),
    path("your_vehicles", views.your_vehicles, name="your_vehicles"),
    path('delete_vehicle/<str:plate_number>/', views.delete_vehicle, name='delete_vehicle'),
    path('checkout', views.checkout, name='checkout'),
]
