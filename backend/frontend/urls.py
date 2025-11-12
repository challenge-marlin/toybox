"""
Frontend app URLs.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/', views.feed, name='feed'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('me/', views.me, name='me'),
    path('lottery/', views.lottery, name='lottery'),
    path('collection/', views.collection, name='collection'),
    path('profile/', views.profile, name='profile'),
    path('profile/view/', views.profile_view, name='profile-view'),
]

