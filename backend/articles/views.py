"""
Articles app views - Ver 2.20
"""
import logging
from django.utils import timezone
from rest_framework import generics, views, status, parsers
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from .models import Article, ArticleReaction, ArticleMedia
from .serializers import ArticleSerializer, ArticleWriteSerializer, ArticleMediaSerializer

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024   # 50 MB
MAX_GIF_SIZE = 10 * 1024 * 1024     # 10 MB

ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTS = {'mp4', 'webm', 'mov'}


class ArticleListCreateView(generics.ListCreateAPIView):
    """記事一覧（公開のみ）＋新規作成。"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Article.objects.select_related('author').prefetch_related('reactions')
        # 自分の下書きも表示する場合
        user = self.request.user
        if user.is_authenticated:
            from django.db.models import Q
            return qs.filter(
                Q(status=Article.Status.PUBLISHED) | Q(author=user)
            )
        return qs.filter(status=Article.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.request.method in ('POST',):
            return ArticleWriteSerializer
        return ArticleSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        out = ArticleSerializer(article, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """記事詳細・更新・削除。"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        qs = Article.objects.select_related('author').prefetch_related('reactions')
        user = self.request.user
        if user.is_authenticated:
            from django.db.models import Q
            return qs.filter(
                Q(status=Article.Status.PUBLISHED) | Q(author=user)
            )
        return qs.filter(status=Article.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ArticleWriteSerializer
        return ArticleSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            return Response({'detail': '権限がありません。'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        out = ArticleSerializer(article, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            return Response({'detail': '権限がありません。'}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArticleReactionView(views.APIView):
    """リアクションの追加・削除。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug, reaction_type):
        try:
            article = Article.objects.get(slug=slug, status=Article.Status.PUBLISHED)
        except Article.DoesNotExist:
            return Response({'detail': '記事が見つかりません。'}, status=status.HTTP_404_NOT_FOUND)

        valid_types = [t.value for t in ArticleReaction.Type]
        if reaction_type not in valid_types:
            return Response({'detail': '不正なリアクションタイプです。'}, status=status.HTTP_400_BAD_REQUEST)

        _, created = ArticleReaction.objects.get_or_create(
            user=request.user, article=article, type=reaction_type
        )

        # 記事著者へのポイント付与（submissions と同様）
        if created and article.author != request.user:
            try:
                from gamification.services import award_reaction_received_points
                award_reaction_received_points(article.author, reaction_type)
            except Exception:
                logger.exception('article reaction pt award failed')

        out = ArticleSerializer(article, context={'request': request})
        return Response({'ok': True, 'created': created, 'article': out.data})

    def delete(self, request, slug, reaction_type):
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            return Response({'detail': '記事が見つかりません。'}, status=status.HTTP_404_NOT_FOUND)
        ArticleReaction.objects.filter(
            user=request.user, article=article, type=reaction_type
        ).delete()
        out = ArticleSerializer(article, context={'request': request})
        return Response({'ok': True, 'article': out.data})


class ArticleMediaUploadView(views.APIView):
    """記事内メディア（画像・動画）アップロード。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'ファイルがありません。'}, status=status.HTTP_400_BAD_REQUEST)

        ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
        is_image = ext in ALLOWED_IMAGE_EXTS
        is_video = ext in ALLOWED_VIDEO_EXTS

        if not is_image and not is_video:
            return Response(
                {'detail': f'対応していないファイル形式です（{ext}）。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = MAX_VIDEO_SIZE if is_video else MAX_IMAGE_SIZE
        if f.size > limit:
            mb = limit // 1024 // 1024
            return Response(
                {'detail': f'ファイルサイズが大きすぎます（最大 {mb}MB）。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        media_type = ArticleMedia.MediaType.VIDEO if is_video else ArticleMedia.MediaType.IMAGE
        obj = ArticleMedia.objects.create(
            uploader=request.user,
            file=f,
            media_type=media_type,
            original_name=f.name[:255],
        )
        serializer = ArticleMediaSerializer(obj, context={'request': request})
        return Response({'ok': True, 'media': serializer.data}, status=status.HTTP_201_CREATED)


class MyArticlesView(generics.ListAPIView):
    """自分の記事一覧（下書き含む）。"""
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializer

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user).select_related('author').prefetch_related('reactions')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
