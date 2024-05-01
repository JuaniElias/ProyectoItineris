from django.urls import path
from . import views

urlpatterns = [
    path('login-user', views.login_user, name='login'),
    path('logout-user', views.logout_user, name='logout'),
    path("sign-up-business", views.sign_up_business, name="sign-up-business"),
]
