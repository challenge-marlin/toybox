"""
Lottery app URLs for DRF.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'lottery', views.LotteryViewSet, basename='lottery')

urlpatterns = [
    path('', include(router.urls)),
]

