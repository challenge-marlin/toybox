"""
Submissions app URLs for DRF.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'submissions', views.SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    # Submit upload endpoint (compatible with Next.js - returns imageUrl/videoUrl)
    path('submit/upload', views.SubmitUploadView.as_view(), name='submit-upload'),
    # Submit game ZIP upload endpoint (extracts ZIP and returns gameUrl)
    path('submit/uploadGame', views.SubmitGameUploadView.as_view(), name='submit-upload-game'),
    # Submit endpoint (compatible with Next.js - returns rewards)
    path('submit/', views.SubmitView.as_view(), name='submit'),
    # Feed endpoint (compatible with Next.js)
    path('feed/', views.FeedView.as_view(), name='feed'),
    # User submissions endpoint
    path('user/submissions/<str:display_id>/', views.UserSubmissionsView.as_view(), name='user-submissions'),
    # Submitters and ranking endpoints
    path('submitters/today/', views.SubmittersTodayView.as_view(), name='submitters-today'),
    path('ranking/daily/', views.RankingDailyView.as_view(), name='ranking-daily'),
    # Timeline endpoint
    path('timeline/', views.TimelineView.as_view(), name='timeline'),
]
