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
        import logging
        logger = logging.getLogger(__name__)
        
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
            
            # 通知を作成（自分で自分にいいねは通知しない）
            if created and submission.author != request.user:
                
                try:
                    target_meta, _ = UserMeta.objects.get_or_create(user=submission.author)
                    liker_meta, _ = UserMeta.objects.get_or_create(user=request.user)
                    
                    liker_name = liker_meta.display_name or liker_meta.bio or request.user.display_id
                    message = f'{liker_name} さんからいいねがつきました'
                    
                    notification = {
                        'type': 'like',
                        'fromAnonId': request.user.display_id,
                        'submissionId': str(submission.id),
                        'message': message,
                        'createdAt': timezone.now().isoformat(),
                        'read': False
                    }
                    
                    # 通知を先頭に追加
                    notifications = target_meta.notifications or []
                    notifications.insert(0, notification)
                    # 最大100件まで保持
                    if len(notifications) > 100:
                        notifications = notifications[:100]
                    target_meta.notifications = notifications
                    target_meta.save()
                    
                    logger.info(f'Notification created: user={submission.author.display_id}, liker={request.user.display_id}, submission={submission.id}')
                except Exception as e:
                    logger.error(f'Failed to create notification: {str(e)}', exc_info=True)
            elif not created:
                logger.debug(f'Like already exists: user={request.user.display_id}, submission={submission.id}')
            
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
        import logging
        logger = logging.getLogger(__name__)
        
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        allowed_video_types = ['video/mp4', 'video/webm', 'video/ogg']
        
        if file.content_type not in allowed_image_types + allowed_video_types:
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file
        is_video = file.content_type in allowed_video_types
        
        # Generate filename
        import os
        if is_video:
            default_ext = '.mp4'
        elif file.content_type == 'image/webp':
            default_ext = '.webp'
        elif file.content_type in ['image/jpeg', 'image/jpg']:
            default_ext = '.jpg'
        else:
            default_ext = '.png'
        file_ext = os.path.splitext(file.name)[1] or default_ext
        filename = f'submissions/{request.user.id}_{int(timezone.now().timestamp())}{file_ext}'
        
        # Save file safely
        from submissions.utils import save_file_safely, build_file_url
        
        success, saved_path, error_message = save_file_safely(file, filename)
        
        if not success:
            logger.error(f'File upload failed: {error_message}')
            return Response({
                'error': 'ファイルの保存に失敗しました',
                'detail': error_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # URLを構築（/uploads/submissions/パスを使用）
        url_path = f'/uploads/submissions/{os.path.basename(saved_path)}'
        absolute_url = build_file_url(request, url_path, base_path='/uploads/submissions/')
        
        logger.info(f'File uploaded successfully: {saved_path} -> {absolute_url}')
        
        # Return URLs compatible with Next.js format
        return Response({
            'imageUrl': absolute_url if not is_video else None,
            'videoUrl': absolute_url if is_video else None,
            'displayImageUrl': absolute_url
        })


class SubmitGameUploadView(APIView):
    """Upload game ZIP file endpoint - extracts and returns gameUrl."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload ZIP file, extract it, and return gameUrl."""
        import logging
        logger = logging.getLogger(__name__)
        
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate ZIP file
        if not file.name.lower().endswith('.zip'):
            return Response({'error': 'ZIP file required'}, status=status.HTTP_400_BAD_REQUEST)
        
        import zipfile
        import os
        import shutil
        from django.conf import settings
        from submissions.utils import normalize_url_path, build_file_url
        
        base_path = None
        try:
            # Get user's display_id for directory structure
            user = request.user
            display_id = user.display_id
            
            # Create directory structure: uploads/games/{display_id}/{timestamp}/
            timestamp = int(timezone.now().timestamp())
            game_dir = f'games/{display_id}/{timestamp}'
            base_path = os.path.join(settings.MEDIA_ROOT, game_dir)
            
            # ディレクトリの存在確認と作成
            try:
                os.makedirs(base_path, exist_ok=True)
                logger.info(f'Created game directory: {base_path}')
            except Exception as e:
                logger.error(f'Failed to create directory {base_path}: {str(e)}', exc_info=True)
                return Response({
                    'error': 'ディレクトリの作成に失敗しました',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Save ZIP file temporarily
            zip_path = os.path.join(base_path, file.name)
            try:
                with open(zip_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                logger.info(f'ZIP file saved: {zip_path}')
            except Exception as e:
                logger.error(f'Failed to save ZIP file {zip_path}: {str(e)}', exc_info=True)
                shutil.rmtree(base_path, ignore_errors=True)
                return Response({
                    'error': 'ZIPファイルの保存に失敗しました',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify ZIP file was saved
            if not os.path.exists(zip_path):
                return Response({
                    'error': 'ZIPファイルの保存に失敗しました'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Audit ZIP file before extraction
            from submissions.utils import audit_zip_file
            audit_result = audit_zip_file(zip_path)
            
            # 監査結果に基づいてエラーまたは警告を返す
            if not audit_result['is_safe']:
                # Clean up on error
                shutil.rmtree(base_path, ignore_errors=True)
                
                error_messages = []
                if audit_result['errors']:
                    error_messages.extend(audit_result['errors'])
                if audit_result['warnings']:
                    error_messages.extend(audit_result['warnings'])
                
                # エラーメッセージを構築
                main_error = 'ZIPファイルの監査に失敗しました'
                if audit_result['errors']:
                    main_error = audit_result['errors'][0]  # 最初のエラーをメインメッセージに
                
                return Response({
                    'error': main_error,
                    'message': main_error,
                    'details': error_messages,
                    'audit_result': {
                        'has_index_html': audit_result['has_index_html'],
                        'suspicious_files': audit_result['suspicious_files'][:10],  # 最初の10個のみ
                        'web_files_count': len(audit_result['web_files'])
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(base_path)
            
            # Remove ZIP file after extraction
            os.remove(zip_path)
            
            # Find index.html
            def find_index_html(directory):
                """Recursively find index.html."""
                for root, dirs, files in os.walk(directory):
                    if 'index.html' in files:
                        return os.path.relpath(os.path.join(root, 'index.html'), settings.MEDIA_ROOT)
                return None
            
            index_path = find_index_html(base_path)
            if not index_path:
                # Clean up on error
                shutil.rmtree(base_path, ignore_errors=True)
                return Response({'error': 'index.html not found in ZIP'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify index.html exists
            index_full_path = os.path.join(settings.MEDIA_ROOT, index_path)
            if not os.path.exists(index_full_path):
                logger.error(f'index.html not found at {index_full_path} after extraction')
                shutil.rmtree(base_path, ignore_errors=True)
                return Response({
                    'error': 'index.htmlが見つかりませんでした'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Convert to URL path (use forward slashes)
            game_url = f'/media/{normalize_url_path(index_path)}'
            
            # Build absolute URL
            absolute_game_url = build_file_url(request, game_url, base_path='/media/')
            
            logger.info(f'Game uploaded successfully: {index_path} -> {absolute_game_url}')
            
            return Response({
                'ok': True,
                'gameUrl': absolute_game_url
            })
            
        except zipfile.BadZipFile:
            if base_path and os.path.exists(base_path):
                shutil.rmtree(base_path, ignore_errors=True)
            return Response({'error': 'Invalid ZIP file'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Failed to process ZIP file: {str(e)}', exc_info=True)
            if base_path and os.path.exists(base_path):
                try:
                    shutil.rmtree(base_path, ignore_errors=True)
                except:
                    pass
            return Response({
                'error': 'ゲームファイルの処理に失敗しました',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubmitView(APIView):
    """Submit endpoint compatible with Next.js - returns rewards (title + card)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle submission and return rewards."""
        user = request.user
        
        # Extract data from request (support both JSON and multipart/form-data)
        aim = request.data.get('aim', '画像提出')
        steps = request.data.get('steps', ['準備', '実行', '完了'])
        # Handle steps: if it's a JSON string (from FormData), parse it
        if isinstance(steps, str):
            try:
                import json
                steps = json.loads(steps)
            except (json.JSONDecodeError, ValueError):
                pass  # Keep original value if parsing fails
        frame_type = request.data.get('frameType', 'none')
        image_url = request.data.get('imageUrl')
        video_url = request.data.get('videoUrl')
        game_url = request.data.get('gameUrl')
        title = request.data.get('title')
        caption = request.data.get('caption')
        hashtags = request.data.get('hashtags')
        
        # Handle hashtags: if it's a JSON string (from FormData), parse it
        if hashtags is not None:
            if isinstance(hashtags, str):
                try:
                    import json
                    hashtags = json.loads(hashtags)
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, treat as single string and convert to list
                    hashtags = [hashtags] if hashtags.strip() else []
            elif not isinstance(hashtags, list):
                # If it's neither string nor list, convert to list
                hashtags = [hashtags] if hashtags else []
        
        # Handle thumbnail file upload (for games)
        thumbnail_file = request.FILES.get('thumbnail')
        thumbnail = None
        if thumbnail_file:
            # Validate thumbnail file type
            allowed_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if thumbnail_file.content_type not in allowed_image_types:
                return Response(
                    {'error': 'サムネイルは画像ファイル（JPEG/PNG/WebP）である必要があります。'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            thumbnail = thumbnail_file
        
        # Handle submission and lottery
        try:
            result = handle_submission_and_lottery(
                user=user,
                aim=aim,
                steps=steps,
                frame_type=frame_type,
                image_url=image_url,
                video_url=video_url,
                game_url=game_url,
                title=title,
                caption=caption,
                hashtags=hashtags,
                thumbnail=thumbnail
            )
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'SubmitView error: {str(e)}', exc_info=True)
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f'SubmitView traceback: {error_detail}')
            return Response({
                'error': '投稿に失敗しました',
                'detail': str(e),
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedView(APIView):
    """Feed endpoint compatible with Next.js format."""
    permission_classes = [IsAuthenticated]  # Require authentication
    
    def get(self, request):
        """Get feed items."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 一般ユーザー（FREE_USER）はアクセスできない
            if hasattr(request.user, 'role') and request.user.role == User.Role.FREE_USER:
                return Response(
                    {'error': 'この機能は課金ユーザー限定です。'},
                    status=status.HTTP_403_FORBIDDEN
                )
            queryset = Submission.objects.filter(deleted_at__isnull=True)
            
            # Filter by hashtag if provided
            hashtag = request.query_params.get('hashtag')
            if hashtag and hashtag.strip():  # 空文字列や空白のみの場合はフィルタリングしない
                hashtag = hashtag.strip()
                # JSONFieldのhashtags配列に指定されたハッシュタグが含まれる投稿をフィルター
                # PostgreSQLのJSONFieldではcontainsを使用（配列に要素が含まれるかチェック）
                try:
                    queryset = queryset.filter(hashtags__contains=[hashtag])
                except Exception as e:
                    # エラーが発生した場合は、Python側でフィルタリング
                    logger.warning(f'Hashtag filter error: {str(e)}, falling back to Python filtering', exc_info=True)
                    # Python側でフィルタリング（非効率だが安全）
                    submission_ids = []
                    for sub in queryset:
                        if sub.hashtags and isinstance(sub.hashtags, list) and hashtag in sub.hashtags:
                            submission_ids.append(sub.id)
                    queryset = queryset.filter(id__in=submission_ids)
            
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
            
            # Annotate with reactions count and select related for performance
            queryset = queryset.select_related('author', 'author__meta').annotate(
                reactions_count=Count('reactions', filter=Q(reactions__type=Reaction.Type.SUBMIT_MEDAL))
            )
            
            # Get items
            items = list(queryset[:limit])
            
            # Serialize items with error handling
            feed_items = []
            for item in items:
                try:
                    serializer = SubmissionSerializer(item, context={'request': request})
                    item_data = serializer.data
                    
                    # Get image URL (シリアライザーのdisplay_image_urlを使用、サムネイル優先)
                    image_url = item_data.get('display_image_url') or item_data.get('image') or item_data.get('image_url')
                    
                    # Get reactions_count from serializer (it will use annotated field if available)
                    reactions_count = item_data.get('reactions_count', 0)
                    
                    # Get display name from UserMeta if available
                    display_name = item_data.get('author_display_id') or 'unknown'
                    try:
                        author = item.author
                        if hasattr(author, 'meta'):
                            meta = author.meta
                            if meta and meta.display_name:
                                display_name = meta.display_name
                            elif meta and meta.bio:
                                display_name = meta.bio
                    except (AttributeError, Exception):
                        pass
                    
                    # Get avatar URL
                    avatar_url = item_data.get('author_avatar_url') or None
                    
                    # Get title - use title field, fallback to caption, but never use "submission"
                    title = item_data.get('title') or None
                    if not title:
                        title = item_data.get('caption') or None
                    
                    feed_items.append({
                        'id': str(item_data.get('id', '')),
                        'anonId': item_data.get('author_display_id') or 'unknown',
                        'displayName': display_name,
                        'avatarUrl': avatar_url,
                        'createdAt': item_data.get('created_at', ''),
                        'imageUrl': image_url,
                        'videoUrl': item_data.get('video_url'),
                        'displayImageUrl': image_url,  # サムネイルが含まれる
                        'title': title,
                        'caption': item_data.get('caption'),
                        'hashtags': item_data.get('hashtags', []),
                        'gameUrl': item_data.get('game_url'),
                        'likesCount': reactions_count or 0,
                        'liked': item_data.get('user_reacted', False),
                    })
                except Exception as e:
                    logger.error(f'Error serializing submission {getattr(item, "id", "unknown")}: {str(e)}', exc_info=True)
                    # エラーが発生した場合はスキップして続行
                    continue
            
            # Determine next cursor
            next_cursor = None
            if len(items) == limit and len(items) > 0:
                try:
                    next_cursor = str(items[-1].id)
                except (AttributeError, IndexError):
                    next_cursor = None
            
            return Response({
                'items': feed_items,
                'nextCursor': next_cursor
            })
        except Exception as e:
            logger.error(f'FeedView error: {str(e)}', exc_info=True)
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f'FeedView traceback: {error_detail}')
            return Response({
                'error': 'フィードの読み込みに失敗しました',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HashtagsView(APIView):
    """Get popular hashtags ordered by usage count."""
    permission_classes = [IsAuthenticated]  # Require authentication
    
    def get(self, request):
        """Get hashtags ordered by usage count."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 一般ユーザー（FREE_USER）はアクセスできない
            if hasattr(request.user, 'role') and request.user.role == User.Role.FREE_USER:
                return Response(
                    {'error': 'この機能は課金ユーザー限定です。'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get limit param (default 20)
            try:
                limit = int(request.query_params.get('limit', 20))
                limit = max(1, min(50, limit))  # Clamp between 1 and 50
            except (ValueError, TypeError):
                limit = 20
            
            # Get all submissions with hashtags
            submissions = Submission.objects.filter(
                deleted_at__isnull=True
            ).exclude(hashtags__isnull=True).exclude(hashtags=[])
            
            # Count hashtag usage
            hashtag_counts = {}
            for submission in submissions:
                if submission.hashtags and isinstance(submission.hashtags, list):
                    for tag in submission.hashtags:
                        if tag and isinstance(tag, str) and tag.strip():
                            tag = tag.strip()
                            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
            
            # Sort by count descending and get top N
            sorted_hashtags = sorted(
                hashtag_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            # Format response
            hashtags = [
                {
                    'tag': tag,
                    'count': count
                }
                for tag, count in sorted_hashtags
            ]
            
            return Response({
                'hashtags': hashtags
            })
        except Exception as e:
            logger.error(f'HashtagsView error: {str(e)}', exc_info=True)
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f'HashtagsView traceback: {error_detail}')
            return Response({
                'error': 'ハッシュタグの取得に失敗しました',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopularFeedView(APIView):
    """Popular feed endpoint - returns submissions ordered by likes count."""
    permission_classes = [IsAuthenticated]  # Require authentication
    
    def get(self, request):
        """Get popular feed items ordered by likes count."""
        # 一般ユーザー（FREE_USER）はアクセスできない
        if hasattr(request.user, 'role') and request.user.role == User.Role.FREE_USER:
            return Response(
                {'error': 'この機能は課金ユーザー限定です。'},
                status=status.HTTP_403_FORBIDDEN
            )
        queryset = Submission.objects.filter(deleted_at__isnull=True)
        
        # Get limit param
        try:
            limit = int(request.query_params.get('limit', 12))
            limit = max(1, min(50, limit))  # Clamp between 1 and 50
        except (ValueError, TypeError):
            limit = 12
        
        # Annotate with reactions count
        queryset = queryset.annotate(
            reactions_count=Count('reactions', filter=Q(reactions__type=Reaction.Type.SUBMIT_MEDAL))
        )
        
        # Order by reactions count descending, then by created_at descending
        queryset = queryset.order_by('-reactions_count', '-created_at')
        
        # Get items
        items = list(queryset[:limit])
        
        # Serialize items
        serializer = SubmissionSerializer(items, many=True, context={'request': request})
        
        # Transform to Next.js format
        feed_items = []
        for idx, item_data in enumerate(serializer.data):
            # Get image URL (シリアライザーのdisplay_image_urlを使用、サムネイル優先)
            image_url = item_data.get('display_image_url') or item_data.get('image') or item_data.get('image_url')
            
            # Get display name from UserMeta if available
            display_name = item_data.get('author_display_id') or 'unknown'
            try:
                # Get the actual item object from the queryset
                if idx < len(items):
                    item_obj = items[idx]
                    author = item_obj.author
                    if hasattr(author, 'meta'):
                        meta = author.meta
                        if meta and meta.display_name:
                            display_name = meta.display_name
                        elif meta and meta.bio:
                            display_name = meta.bio
            except (AttributeError, Exception, IndexError):
                pass
            
            # Get avatar URL
            avatar_url = item_data.get('author_avatar_url') or None
            
            # Get title - use title field, fallback to caption, but never use "submission"
            title = item_data.get('title') or None
            if not title:
                title = item_data.get('caption') or None
            
            feed_items.append({
                'id': str(item_data['id']),
                'anonId': item_data.get('author_display_id') or 'unknown',
                'displayName': display_name,
                'avatarUrl': avatar_url,
                'createdAt': item_data['created_at'],
                'imageUrl': image_url,
                'videoUrl': item_data.get('video_url'),
                'displayImageUrl': image_url,  # サムネイルが含まれる
                'title': title,
                'caption': item_data.get('caption'),
                'hashtags': item_data.get('hashtags', []),
                'gameUrl': item_data.get('game_url'),
                'likesCount': item_data.get('reactions_count', 0),
                'liked': item_data.get('user_reacted', False),
            })
        
        return Response({
            'items': feed_items
        })


class UserSubmissionsView(APIView):
    """Get user's submissions by display_id."""
    permission_classes = [AllowAny]
    
    def get(self, request, display_id):
        """Get submissions for a specific user."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
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
                    cursor_date = datetime.fromisoformat(cursor.replace('Z', '+00:00'))
                    # Make timezone-aware if needed
                    if timezone.is_naive(cursor_date):
                        cursor_date = timezone.make_aware(cursor_date)
                    queryset = queryset.filter(created_at__lt=cursor_date)
                except (ValueError, AttributeError, TypeError):
                    pass
            
            submissions = queryset[:page_size]
            
            # Check if current user has liked each submission
            current_user = request.user if request.user.is_authenticated else None
            
            # Format response
            items = []
            for sub in submissions:
                try:
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
                    
                    # Get image/video/game URL (absolute URLs)
                    # ゲームの場合はサムネイルを優先
                    image_url = None
                    display_image_url = None
                    
                    try:
                        if sub.game_url:
                            # ゲームの場合：サムネイルを優先
                            if sub.thumbnail:
                                try:
                                    display_image_url = request.build_absolute_uri(sub.thumbnail.url)
                                    image_url = display_image_url
                                except (ValueError, AttributeError):
                                    # thumbnail.urlが無効な場合のフォールバック
                                    if sub.image_url:
                                        display_image_url = sub.image_url
                                        image_url = sub.image_url
                                    elif sub.image:
                                        try:
                                            display_image_url = request.build_absolute_uri(sub.image.url)
                                            image_url = display_image_url
                                        except (ValueError, AttributeError):
                                            pass
                            elif sub.image_url:
                                display_image_url = sub.image_url
                                image_url = sub.image_url
                            elif sub.image:
                                try:
                                    display_image_url = request.build_absolute_uri(sub.image.url)
                                    image_url = display_image_url
                                except (ValueError, AttributeError):
                                    pass
                        else:
                            # 画像/動画の場合：従来通り
                            if sub.image_url:
                                image_url = sub.image_url
                                display_image_url = sub.image_url
                            elif sub.image:
                                try:
                                    image_url = request.build_absolute_uri(sub.image.url)
                                    display_image_url = image_url
                                except (ValueError, AttributeError):
                                    pass
                    except Exception as e:
                        logger.warning(f'Error processing image URLs for submission {sub.id}: {str(e)}')
                    
                    video_url = getattr(sub, 'video_url', None) if getattr(sub, 'video_url', None) else None
                    game_url = getattr(sub, 'game_url', None) if getattr(sub, 'game_url', None) else None
                    
                    # Safely get title and caption
                    title = getattr(sub, 'title', None) or None
                    caption = getattr(sub, 'caption', None) or None
                    
                    # Safely format created_at
                    created_at_str = None
                    try:
                        created_at = getattr(sub, 'created_at', None)
                        if created_at:
                            created_at_str = created_at.isoformat()
                    except (AttributeError, ValueError, TypeError):
                        created_at_str = None
                    
                    items.append({
                        'id': str(sub.id),
                        'imageUrl': image_url,
                        'displayImageUrl': display_image_url or image_url,
                        'videoUrl': video_url,
                        'gameUrl': game_url,
                        'title': title,
                        'caption': caption,
                        'createdAt': created_at_str,
                        'likesCount': likes_count,
                        'liked': liked,
                    })
                except Exception as e:
                    logger.error(f'Error processing submission {sub.id}: {str(e)}', exc_info=True)
                    # エラーが発生しても次の提出物の処理を続行
                    continue
            
            next_cursor = None
            if len(submissions) == page_size:
                try:
                    last_submission = submissions[-1]
                    if last_submission.created_at:
                        next_cursor = last_submission.created_at.isoformat()
                except (AttributeError, ValueError, IndexError):
                    next_cursor = None
            
            return Response({
                'items': items,
                'nextCursor': next_cursor
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f'UserSubmissionsView error for display_id={display_id}: {str(e)}', exc_info=True)
            logger.error(f'UserSubmissionsView traceback: {error_traceback}')
            # 開発環境では詳細なエラー情報を返す
            import os
            if os.environ.get('DEBUG', 'False').lower() == 'true':
                return Response(
                    {
                        'error': '提出物の読み込みに失敗しました。',
                        'details': str(e),
                        'traceback': error_traceback
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                return Response(
                    {'error': '提出物の読み込みに失敗しました。', 'details': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


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
                
                # Get display name from display_name field, fallback to display_id
                display_name = None
                if meta and meta.display_name:
                    display_name = meta.display_name
                else:
                    display_name = user.display_id
                
                submitters.append({
                    'anonId': user.display_id,
                    'displayName': display_name
                })
            except User.DoesNotExist:
                continue
        
        return Response({
            'submitters': submitters,
            'count': len(submitters)
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
                
                # Get display name from display_name field, fallback to display_id
                display_name = None
                if meta and meta.display_name:
                    display_name = meta.display_name
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


class TimelineView(APIView):
    """Get timeline of recent submissions."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get recent submissions for timeline."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get pagination params
            try:
                limit = int(request.query_params.get('limit', 10))
                limit = max(1, min(50, limit))  # Clamp between 1 and 50
            except (ValueError, TypeError):
                limit = 10
            
            cursor = request.query_params.get('cursor')
            
            queryset = Submission.objects.filter(
                deleted_at__isnull=True
            ).select_related('author').order_by('-created_at')
            
            # If cursor provided, decode and filter
            if cursor:
                try:
                    cursor_id = int(cursor)
                    queryset = queryset.filter(id__lt=cursor_id)
                except (ValueError, TypeError):
                    pass
            
            # Get items
            submissions = list(queryset[:limit])
            
            timeline_items = []
            for sub in submissions:
                try:
                    # Get UserMeta if it exists
                    try:
                        meta = sub.author.meta
                    except AttributeError:
                        meta = None
                    
                    # Get display name from display_name field, fallback to display_id
                    display_name = None
                    if meta and hasattr(meta, 'display_name') and meta.display_name:
                        display_name = meta.display_name
                    else:
                        display_name = sub.author.display_id
                    
                    # Determine submission type
                    submission_type = '画像'
                    if sub.game_url:
                        submission_type = 'ゲーム'
                    elif sub.video_url:
                        submission_type = '動画'
                    elif sub.image_url or sub.image:
                        submission_type = '画像'
                    
                    # Get avatar URL
                    avatar_url = None
                    if hasattr(sub.author, 'avatar_url') and sub.author.avatar_url:
                        avatar_url = sub.author.avatar_url
                    
                    timeline_items.append({
                        'id': str(sub.id),
                        'anonId': sub.author.display_id,
                        'displayName': display_name,
                        'avatarUrl': avatar_url,
                        'type': submission_type,
                        'createdAt': sub.created_at.isoformat(),
                    })
                except Exception as e:
                    logger.error(f'Error processing timeline item {sub.id}: {str(e)}', exc_info=True)
                    continue
            
            # Determine next cursor
            next_cursor = None
            if len(submissions) == limit and submissions:
                next_cursor = str(submissions[-1].id)
            
            return Response({
                'items': timeline_items,
                'nextCursor': next_cursor
            })
        except Exception as e:
            logger.error(f'TimelineView error: {str(e)}', exc_info=True)
            return Response(
                {'error': 'タイムラインの読み込みに失敗しました。', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
