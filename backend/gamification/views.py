"""
Gamification views.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import UserMeta, UserCard
from gamification.models import Card
from .services import load_card_master
from django.db.models import Count, Q

class GenerateCardView(views.APIView):
    """Generate a card."""
    
    def post(self, request):
        # Card generation logic
        return Response({'error': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MyCardsView(views.APIView):
    """Get user's cards."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's card collection."""
        user_cards = UserCard.objects.filter(user=request.user).select_related('card')
        
        # Map Django rarity to Next.js format
        rarity_map = {
            'common': 'N',
            'rare': 'R',
            'seasonal': 'SR',
            'special': 'SSR'
        }
        
        # Group cards by card code and count quantity
        card_groups = {}
        for uc in user_cards:
            card = uc.card
            card_code = card.code
            
            if card_code not in card_groups:
                rarity_str = rarity_map.get(card.rarity, 'N')
                card_type = 'Effect' if card.code.startswith('E') else 'Character'
                
                card_groups[card_code] = {
                    'id': card_code,
                    'obtainedAt': uc.obtained_at.isoformat() if uc.obtained_at else None,
                    'quantity': 0,
                    'meta': {
                        'card_id': card_code,
                        'card_type': card_type,
                        'card_name': card.name,
                        'rarity': rarity_str,
                        'image_url': card.image_url or f'/uploads/cards/{card.code}.png'
                    }
                }
            
            # Increment quantity
            card_groups[card_code]['quantity'] += 1
            
            # Update obtainedAt to the most recent one
            if uc.obtained_at:
                current_obtained = card_groups[card_code]['obtainedAt']
                if not current_obtained or uc.obtained_at.isoformat() > current_obtained:
                    card_groups[card_code]['obtainedAt'] = uc.obtained_at.isoformat()
        
        entries = list(card_groups.values())
        
        return Response({'ok': True, 'entries': entries})


class CardsSummaryView(views.APIView):
    """Get cards summary."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's card collection summary."""
        user_cards = UserCard.objects.filter(user=request.user).select_related('card')
        
        # Count by rarity
        rarity_map = {
            'common': 'N',
            'rare': 'R',
            'seasonal': 'SR',
            'special': 'SSR'
        }
        
        rarity_counts = {'SSR': 0, 'SR': 0, 'R': 0, 'N': 0}
        for uc in user_cards:
            rarity_str = rarity_map.get(uc.card.rarity, 'N')
            rarity_counts[rarity_str] = rarity_counts.get(rarity_str, 0) + 1
        
        return Response({
            'ok': True,
            'total': user_cards.count(),
            'rarity': rarity_counts,
            'byAttr': {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}  # TODO: implement attribute counting
        })

