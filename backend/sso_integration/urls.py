from django.urls import path

from . import views

urlpatterns = [
    path("callback/", views.sso_callback, name="sso-callback"),
    path("login/", views.sso_login, name="sso-login"),
    path("dispatch/<str:target_system>/", views.sso_dispatch, name="sso-dispatch"),
]
