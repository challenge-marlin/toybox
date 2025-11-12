"""
Submissions app views for DRF.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import Submission, Reaction
from .serializers import SubmissionSerializer, SubmissionCreateSerializer, ReactionSerializer
from users.models import UserMeta, User
from lottery.services import handle_submission_and_lottery


class SubmissionViewSet(viewsets.ModelViewSet):
    """Submission viewset."""
    queryset = Submission.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'comment_enabled']
    search_fields = ['caption']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return SubmissionCreateSerializer
        return SubmissionSerializer
    
    def get_queryset(self):
        """Filter submissions based on query params."""
        queryset = super().get_queryset()
        
        # Filter by day (today)
        from datetime import datetime
        day = self.request.query_params.get('day')
        if day == 'today':
            today = timezone.now().date()
            start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
            end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
            queryset = queryset.filter(created_at__gte=start, created_at__lte=end)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create submission with current user as author."""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='react/submit_medal')
    def react_submit_medal(self, request, pk=None):
        """React to submission with submit_medal."""
        submission = self.get_object()
        
        # Check if already reacted
        reaction, created = Reaction.objects.get_or_create(
            user=request.user,
            submission=submission,
            type=Reaction.Type.SUBMIT_MEDAL,
            defaults={'user': request.user, 'submission': submission}
        )
        
        if created:
            return Response({'ok': True, 'message': 'Reaction added'}, status=status.HTTP_201_CREATED)
        else:
            reaction.delete()
            return Response({'ok': True, 'message': 'Reaction removed'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post', 'delete'], url_path='like')
    def like(self, request, pk=None):
        """Like/unlike submission (compatible with Next.js API)."""
        submission = self.get_object()
        
        if request.method == 'POST':
            # Like
            reaction, created = Reaction.objects.get_or_create(
                user=request.user,
                submission=submission,
                type=Reaction.Type.SUBMIT_MEDAL,
                defaults={'user': request.user, 'submission': submission}
            )
            
            likes_count = Reaction.objects.filter(
                submission=submission,
                type=Reaction.Type.SUBMIT_MEDAL
            ).count()
            
            return Response({
                'ok': True,
                'likesCount': likes_count,
                'liked': True
            })
        else:
            # Unlike (DELETE)
            Reaction.objects.filter(
                user=request.user,
                submission=submission,
                type=Reaction.Type.SUBMIT_MEDAL
            ).delete()
            
            likes_count = Reaction.objects.filter(
                submission=submission,
                type=Reaction.Type.SUBMIT_MEDAL
            ).count()
            
            return Response({
                'ok': True,
                'likesCount': likes_count,
                'liked': False
            })
    
    @action(detail=True, methods=['post'], url_path='comments/toggle')
    def toggle_comments(self, request, pk=None):
        """Toggle comment_enabled (owner only)."""
        submission = self.get_object()
        
        if submission.author != request.user:
            return Response(
                {'error': 'Only submission owner can toggle comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submission.comment_enabled = not submission.comment_enabled
        submission.save()
        
        return Response({
            'ok': True,
            'comment_enabled': submission.comment_enabled
        })


class SubmitUploadView(APIView):
    """Upload file endpoint compatible with Next.js - returns imageUrl/videoUrl."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload file and return URL."""
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_image_types = ['image/jpeg', 'image/jpg', 'image/png']
        allowed_video_types = ['video/mp4', 'video/webm', 'video/ogg']
        
        if file.content_type not in allowed_image_types + allowed_video_types:
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file
        is_video = file.content_type in allowed_video_types
        
        # Use Django's default storage to save the file temporarily
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        
        # Generate filename
        file_ext = os.path.splitext(file.name)[1] or ('.mp4' if is_video else '.png')
        filename = f'submissions/{request.user.id}_{int(timezone.now().timestamp())}{file_ext}'
        
        # Save file
        saved_path = default_storage.save(filename, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)
        
        # Build absolute URL
        absolute_url = request.build_absolute_uri(file_url)
        
        # Return URLs compatible with Next.js format
        return Response({
            'imageUrl': absolute_url if not is_video else None,
            'videoUrl': absolute_url if is_video else None,
            'displayImageUrl': absolute_url
        })


class SubmitView(APIView):
    """Submit endpoint compatible with Next.js - returns rewards (title + card)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle submission and return rewards."""
        user = request.user
        
        # Extract data from request
        aim = request.data.get('aim', '画像提出')
        steps = request.data.get('steps', ['準備', '実行', '完了'])
        frame_type = request.data.get('frameType', 'none')
        image_url = request.data.get('imageUrl')
        video_url = request.data.get('videoUrl')
        game_url = request.data.get('gameUrl')
        
        # Handle submission and lottery
        result = handle_submission_and_lottery(
            user=user,
            aim=aim,
            steps=steps,
            frame_type=frame_type,
            image_url=image_url,
            video_url=video_url,
            game_url=game_url
        )
        
        return Response(result)


class FeedView(APIView):
    """Feed endpoint compatible with Next.js format."""
    permission_classes = [AllowAny]  # Allow anonymous access
    
    def get(self, request):
        """Get feed items."""
        queryset = Submission.objects.filter(deleted_at__isnull=True)
        
        # Get pagination params
        try:
            limit = int(request.query_params.get('limit', 24))
            limit = max(1, min(50, limit))  # Clamp between 1 and 50
        except (ValueError, TypeError):
            limit = 24
        
        cursor = request.query_params.get('cursor')
        
        # If cursor provided, decode and filter
        if cursor:
            try:
                # Cursor is typically the last item's ID or timestamp
                # For simplicity, we'll use ID-based pagination
                cursor_id = int(cursor)
                queryset = queryset.filter(id__lt=cursor_id)
            except (ValueError, TypeError):
                pass
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Annotate with reactions count
        queryset = queryset.annotate(
            reactions_count=Count('reactions', filter=Q(reactions__type=Reaction.Type.SUBMIT_MEDAL))
        )
        
        # Get items
        items = queryset[:limit]
        
        # Serialize items
        serializer = SubmissionSerializer(items, many=True, context={'request': request})
        
        # Determine next cursor
        next_cursor = None
        if len(items) == limit:
            next_cursor = str(items[-1].id)
        
        # Transform to Next.js format
        feed_items = []
        for item_data in serializer.data:
            feed_items.append({
                'id': str(item_data['id']),
                'anonId': item_data.get('author_display_id') or 'unknown',
                'displayName': item_data.get('author_display_id'),
                'createdAt': item_data['created_at'],
                'imageUrl': item_data.get('image'),
                'videoUrl': None,  # TODO: Add video support
                'displayImageUrl': item_data.get('image'),
                'title': item_data.get('caption'),
                'gameUrl': None,  # TODO: Add game URL support
                'likesCount': item_data.get('reactions_count', 0),
                'liked': item_data.get('user_reacted', False),
            })
        
        return Response({
            'items': feed_items,
            'nextCursor': next_cursor
        })


class UserSubmissionsView(APIView):
    """Get user's submissions by display_id."""
    permission_classes = [AllowAny]
    
    def get(self, request, display_id):
        """Get submissions for a specific user."""
        try:
            user = User.objects.get(display_id=display_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset = Submission.objects.filter(
            author=user,
            deleted_at__isnull=True
        ).select_related('author', 'author__meta').order_by('-created_at')
        
        # Pagination
        page_size = int(request.query_params.get('limit', 12))
        cursor = request.query_params.get('cursor')
        
        if cursor:
            try:
                from datetime import datetime
                cursor_date = timezone.datetime.fromisoformat(cursor.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__lt=cursor_date)
            except (ValueError, AttributeError):
                pass
        
        submissions = queryset[:page_size]
        
        # Check if current user has liked each submission
        current_user = request.user if request.user.is_authenticated else None
        
        # Format response
        items = []
        for sub in submissions:
            # Count likes
            likes_count = Reaction.objects.filter(
                submission=sub,
                type=Reaction.Type.SUBMIT_MEDAL
            ).count()
            
            # Check if current user liked
            liked = False
            if current_user:
                liked = Reaction.objects.filter(
                    user=current_user,
                    submission=sub,
                    type=Reaction.Type.SUBMIT_MEDAL
                ).exists()
            
            # Get image/video/game URL
            image_url = sub.image.url if sub.image else (sub.image_url if sub.image_url else None)
            video_url = sub.video_url if sub.video_url else None
            game_url = sub.game_url if sub.game_url else None
            
            items.append({
                'id': str(sub.id),
                'imageUrl': image_url,
                'displayImageUrl': image_url,
                'videoUrl': video_url,
                'gameUrl': game_url,
                'createdAt': sub.created_at.isoformat(),
                'likesCount': likes_count,
                'liked': liked,
            })
        
        next_cursor = None
        if len(submissions) == page_size:
            next_cursor = submissions[-1].created_at.isoformat()
        
        return Response({
            'items': items,
            'nextCursor': next_cursor
        })


class SubmittersTodayView(APIView):
    """Get today's submitters list."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of users who submitted today."""
        from datetime import datetime
        
        today = timezone.now().date()
        start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Get unique users who submitted today
        user_ids = Submission.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            deleted_at__isnull=True
        ).values_list('author', flat=True).distinct()
        
        submitters = []
        for user_id in user_ids:
            try:
                user = User.objects.select_related('meta').get(id=user_id)
                meta = getattr(user, 'meta', None)
                
                # Get display name from bio field (which stores display_name) or fallback to display_id
                display_name = None
                if meta and meta.bio:
                    display_name = meta.bio
                else:
                    display_name = user.display_id
                
                submitters.append({
                    'anonId': user.display_id,
                    'displayName': display_name
                })
            except User.DoesNotExist:
                continue
        
        return Response({
            'submitters': submitters
        })


class RankingDailyView(APIView):
    """Get daily ranking of submissions."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get daily ranking by submission count."""
        from datetime import datetime
        
        today = timezone.now().date()
        start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Count submissions per user for today
        submissions = Submission.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            deleted_at__isnull=True
        ).values('author').annotate(count=Count('id')).order_by('-count')[:10]
        
        ranking = []
        for sub_data in submissions:
            user_id = sub_data['author']
            count = sub_data['count']
            try:
                user = User.objects.select_related('meta').get(id=user_id)
                meta = getattr(user, 'meta', None)
                
                # Get display name from bio field (which stores display_name) or fallback to display_id
                display_name = None
                if meta and meta.bio:
                    display_name = meta.bio
                else:
                    display_name = user.display_id
                
                ranking.append({
                    'anonId': user.display_id,
                    'displayName': display_name,
                    'count': count
                })
            except User.DoesNotExist:
                continue
        
        return Response({
            'ranking': ranking
        })
    
