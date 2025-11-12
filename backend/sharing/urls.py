"""
Sharing URLs.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('discord/', views.DiscordShareView.as_view(), name='discord-share'),
]

