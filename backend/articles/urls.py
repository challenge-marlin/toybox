"""
Articles app URLs - Ver 2.22
"""
from django.urls import path
from . import views

urlpatterns = [
    # 記事一覧・作成
    path('', views.ArticleListCreateView.as_view(), name='article-list-create'),
    # 自分の記事（下書き含む）
    path('mine/', views.MyArticlesView.as_view(), name='article-mine'),
    # メディアアップロード
    path('upload-media/', views.ArticleMediaUploadView.as_view(), name='article-media-upload'),
    path('upload-media', views.ArticleMediaUploadView.as_view(), name='article-media-upload-noslash'),
    # 記事詳細・更新・削除（slug でアクセス）
    path('<str:slug>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('<str:slug>', views.ArticleDetailView.as_view(), name='article-detail-noslash'),
    # リアクション
    path('<str:slug>/react/<str:reaction_type>/', views.ArticleReactionView.as_view(), name='article-react'),
    path('<str:slug>/react/<str:reaction_type>', views.ArticleReactionView.as_view(), name='article-react-noslash'),
]
