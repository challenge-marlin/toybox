"""
Frontend app URLs.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/', views.feed, name='feed'),
    path('login/', views.login_page, name='login'),
    path('me/', views.me, name='me'),
    path('lottery/', views.lottery, name='lottery'),
]
