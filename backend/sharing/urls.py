"""
Sharing URLs.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('discord/', views.DiscordShareView.as_view(), name='discord-share'),
    path('discord/status/', views.DiscordStatusView.as_view(), name='discord-share-status'),
]

