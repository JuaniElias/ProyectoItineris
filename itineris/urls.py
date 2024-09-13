from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("work_with_us", views.work_with_us, name="work_with_us"),
    path("about_us", views.about, name="about_us"),
    path("create_travel", views.create_travel, name="create_travel"),
    path("show_waypoints", views.show_waypoints, name="show_waypoints"),
    path("add_waypoint", views.add_waypoint, name="add_waypoint"),
    path("delete_waypoint/<str:waypoint_id>/", views.delete_waypoint, name="delete_waypoint"),
    path("show_segments/", views.show_segments, name="show_segments"),
    path("generate_segments/", views.generate_segments, name="generate_segments"),
    path("end_travel_creation/", views.end_travel_creation, name="end_travel_creation"),
    path("get_available_options", views.get_available_options, name="get_available_options"),
    path("travel_result", views.travel_result, name="travel_result"),
    path("travel_result_failed", views.travel_result_failed, name="travel_result_failed"),
    path("show_travelers", views.show_travelers, name="show_travelers"),
    path("pre_checkout/<str:segment_id>/", views.pre_checkout, name="pre_checkout"),
    path("your_drivers", views.your_drivers, name="your_drivers"),
    path("delete_driver/<str:driver_id>/", views.delete_driver, name="delete_driver"),
    path("edit_driver/<str:driver_id>/", views.edit_driver, name="edit_driver"),
    path("your_travels", views.your_travels, name="your_travels"),
    path("travel_detail/<str:travel_id>/", views.travel_detail, name="travel_detail"),
    path("mark_travel_ended/<str:travel_id>/", views.mark_travel_ended, name="mark_travel_ended"),
    path("start_trip/<str:travel_id>/", views.start_trip, name="start_trip"),
    path("your_vehicles", views.your_vehicles, name="your_vehicles"),
    path("delete_vehicle/<str:plate_number>/", views.delete_vehicle, name="delete_vehicle"),
    path("checkout", views.checkout, name="checkout"),
    path("travel_history", views.travel_history, name="travel_history"),
    path("payment_success", views.payment_success, name="payment_success"),
    path("feedback/<str:encrypted_traveler_id>/", views.feedback, name="feedback"),
    path("update_feedback/", views.update_feedback, name="update_feedback"),
    path("update_traveler/<str:encrypted_traveler_id>/", views.update_traveler, name="update_traveler"),
    path("cancel_traveler_ticket/<str:encrypted_traveler_id>/", views.cancel_traveler_ticket,
         name="cancel_traveler_ticket"),
    path("update_travel/<str:travel_id>/", views.update_travel, name="update_travel"),
    path("cancel_travel_handler/<str:travel_id>/", views.cancel_travel_handler, name="cancel_travel_handler"),
    path("export_travelers_to_csv/<str:travel_id>/", views.export_travelers_to_csv, name="export_travelers_to_csv"),
]
