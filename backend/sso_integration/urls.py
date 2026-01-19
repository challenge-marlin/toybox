from django.urls import path

from . import views

urlpatterns = [
    path("callback/", views.sso_callback, name="sso-callback"),
    path("login/", views.sso_login, name="sso-login"),
    path("dispatch/<str:target_system>/", views.sso_dispatch, name="sso-dispatch"),
    path("verify-and-check/", views.sso_verify_and_check, name="sso-verify-and-check"),
    path("login-with-ticket/", views.sso_login_with_ticket, name="sso-login-with-ticket"),
]
