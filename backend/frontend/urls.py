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
    path('upgrade/', views.upgrade, name='upgrade'),
    path('lottery/', views.lottery, name='lottery'),
    path('collection/', views.collection, name='collection'),
    path('profile/', views.profile, name='profile'),
    path('profile/view/', views.profile_view, name='profile-view'),
    path('announcements/', views.announcements_list, name='announcements-list'),
    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement-detail'),
    path('terms/', views.terms, name='terms'),
    path('terms/agree/', views.terms_agree, name='terms-agree'),
    path('inquiry/', views.inquiry, name='inquiry'),
    path('derivative-guidelines/', views.derivative_guidelines, name='derivative-guidelines'),
    path('privacy/', views.privacy, name='privacy'),
]

