"""
Gamification URLs.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.GenerateCardView.as_view(), name='generate-card'),
    path('me/', views.MyCardsView.as_view(), name='my-cards'),
    path('summary/', views.CardsSummaryView.as_view(), name='cards-summary'),
]

