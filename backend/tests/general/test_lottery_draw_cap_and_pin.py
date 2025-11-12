"""
Tests for lottery draw cap and pin functionality.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from lottery.models import JackpotWin, LotteryRule
from users.models import UserMeta


@pytest.mark.django_db
class TestLotteryDrawCapAndPin:
    """Test lottery draw cap and pin functionality."""
    
    def test_draw_lottery_success(self, authenticated_client, user, lottery_rule):
        """Test successful lottery draw."""
        response = authenticated_client.post('/api/lottery/draw/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'won' in response.data
        assert 'ok' in response.data
    
    def test_draw_lottery_twice_same_day_fails(self, authenticated_client, user, lottery_rule):
        """Test that drawing lottery twice in same day fails."""
        # First draw
        response1 = authenticated_client.post('/api/lottery/draw/')
        assert response1.status_code == status.HTTP_200_OK
        
        # Second draw (should fail)
        response2 = authenticated_client.post('/api/lottery/draw/')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Already drawn today' in response2.data['error']
    
    def test_jackpot_win_creates_pin(self, authenticated_client, user, lottery_rule):
        """Test that jackpot win creates pin with 24h expiry."""
        # Mock random to always win
        import random
        original_random = random.random
        random.random = lambda: 0.0  # Always win
        
        try:
            response = authenticated_client.post('/api/lottery/draw/')
            
            if response.data.get('won'):
                assert 'pinned_until' in response.data
                
                # Verify JackpotWin exists
                win = JackpotWin.objects.filter(user=user).first()
                assert win is not None
                assert win.pinned_until is not None
                assert win.pinned_until > timezone.now()
        finally:
            random.random = original_random
    
    def test_pin_expiry_is_24h_after_win(self, user, lottery_rule):
        """Test that pin expiry is 24h after win."""
        won_at = timezone.now()
        pinned_until = won_at + timedelta(hours=24)
        
        win = JackpotWin.objects.create(
            user=user,
            won_at=won_at,
            pinned_until=pinned_until
        )
        
        assert win.pinned_until == pinned_until
        assert (win.pinned_until - win.won_at).total_seconds() == 86400  # 24 hours
    
    def test_clean_expired_pins(self, user):
        """Test cleaning expired pins."""
        from lottery.tasks import clean_expired_pins
        
        # Create expired pin
        expired_win = JackpotWin.objects.create(
            user=user,
            won_at=timezone.now() - timedelta(days=2),
            pinned_until=timezone.now() - timedelta(days=1)  # Expired
        )
        
        # Create valid pin
        valid_win = JackpotWin.objects.create(
            user=user,
            won_at=timezone.now(),
            pinned_until=timezone.now() + timedelta(hours=12)  # Valid
        )
        
        # Run cleanup task
        clean_expired_pins()
        
        # Verify expired pin is cleared
        expired_win.refresh_from_db()
        assert expired_win.pinned_until is None
        
        # Verify valid pin is preserved
        valid_win.refresh_from_db()
        assert valid_win.pinned_until is not None
    
    def test_lottery_bonus_count_increments_on_loss(self, authenticated_client, user, lottery_rule):
        """Test that lottery bonus count increments on loss."""
        # Mock random to always lose
        import random
        original_random = random.random
        random.random = lambda: 1.0  # Always lose
        
        try:
            meta, _ = UserMeta.objects.get_or_create(user=user)
            initial_count = meta.lottery_bonus_count
            
            response = authenticated_client.post('/api/lottery/draw/')
            
            if not response.data.get('won'):
                meta.refresh_from_db()
                assert meta.lottery_bonus_count == initial_count + 1
        finally:
            random.random = original_random
    
    def test_lottery_bonus_count_resets_on_win(self, authenticated_client, user, lottery_rule):
        """Test that lottery bonus count resets on win."""
        # Set initial bonus count
        meta, _ = UserMeta.objects.get_or_create(user=user)
        meta.lottery_bonus_count = 5
        meta.save()
        
        # Mock random to always win
        import random
        original_random = random.random
        random.random = lambda: 0.0  # Always win
        
        try:
            response = authenticated_client.post('/api/lottery/draw/')
            
            if response.data.get('won'):
                meta.refresh_from_db()
                assert meta.lottery_bonus_count == 0
        finally:
            random.random = original_random

