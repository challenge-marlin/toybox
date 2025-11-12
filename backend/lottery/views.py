"""
Lottery app views for DRF.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import LotteryRule, JackpotWin
from users.models import UserMeta


class LotteryViewSet(viewsets.ViewSet):
    """Lottery viewset."""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def draw(self, request):
        """Draw lottery (once per day)."""
        user = request.user
        
        # Check if already drawn today
        from datetime import datetime
        today = timezone.now().date()
        start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        existing_win = JackpotWin.objects.filter(
            user=user,
            won_at__gte=start,
            won_at__lte=end
        ).first()
        
        if existing_win:
            return Response(
                {'error': 'Already drawn today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active lottery rule
        rule = LotteryRule.objects.filter(is_active=True).first()
        if not rule:
            return Response(
                {'error': 'No active lottery rule'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Calculate probability (simplified)
        user_meta, _ = UserMeta.objects.get_or_create(user=user)
        consecutive_loses = user_meta.lottery_bonus_count
        
        probability = float(rule.base_rate) + (float(rule.per_submit_increment) * consecutive_loses)
        probability = min(probability, float(rule.max_rate))
        
        # Draw
        import random
        won = random.random() < probability
        
        if won:
            # Create JackpotWin
            pinned_until = timezone.now() + timezone.timedelta(hours=24)
            jackpot_win = JackpotWin.objects.create(
                user=user,
                won_at=timezone.now(),
                pinned_until=pinned_until
            )
            
            # Reset bonus count
            user_meta.lottery_bonus_count = 0
            user_meta.save()
            
            return Response({
                'ok': True,
                'won': True,
                'jackpot_win_id': jackpot_win.id,
                'pinned_until': pinned_until.isoformat()
            })
        else:
            # Increment bonus count
            user_meta.lottery_bonus_count += 1
            user_meta.save()
            
            return Response({
                'ok': True,
                'won': False,
                'probability': probability,
                'bonus_count': user_meta.lottery_bonus_count
            })

