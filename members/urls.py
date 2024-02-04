from django.urls import path
from . import views

urlpatterns = [
    path('login_user', views.login_user, name='login'),
    path('logout_user', views.logout_user, name='logout'),
    path('signup_user', views.signup_user, name='sign-up'),
    path("sign-up-business", views.signup_business, name="sign-up-business"),
]
