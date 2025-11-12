"""
Tests for user meta expiry.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from users.models import UserMeta
from lottery.tasks import expire_user_titles_daily


@pytest.mark.django_db
class TestUserMetaExpiry:
    """Test user meta title expiry."""
    
    def test_expired_title_is_cleared(self, user):
        """Test that expired title is cleared."""
        # Create user meta with expired title
        meta = UserMeta.objects.create(
            user=user,
            active_title='Expired Title',
            title_color='#FF0000',
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )
        
        # Run expiry task
        expire_user_titles_daily()
        
        # Verify title is cleared
        meta.refresh_from_db()
        assert meta.active_title is None
        assert meta.title_color is None
        assert meta.expires_at is None
    
    def test_valid_title_is_preserved(self, user):
        """Test that valid title is preserved."""
        # Create user meta with valid title
        meta = UserMeta.objects.create(
            user=user,
            active_title='Valid Title',
            title_color='#00FF00',
            expires_at=timezone.now() + timedelta(days=7)  # Valid
        )
        
        # Run expiry task
        expire_user_titles_daily()
        
        # Verify title is preserved
        meta.refresh_from_db()
        assert meta.active_title == 'Valid Title'
        assert meta.title_color == '#00FF00'
    
    def test_get_user_meta_expires_expired_title(self, authenticated_client, user):
        """Test that expired title is cleared when fetching user meta."""
        # Create user meta with expired title
        meta = UserMeta.objects.create(
            user=user,
            active_title='Expired Title',
            title_color='#FF0000',
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Fetch user meta
        response = authenticated_client.get('/api/users/me/meta/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify title is cleared
        meta.refresh_from_db()
        assert meta.active_title is None
    
    def test_get_user_meta_preserves_valid_title(self, authenticated_client, user):
        """Test that valid title is preserved when fetching user meta."""
        # Create user meta with valid title
        meta = UserMeta.objects.create(
            user=user,
            active_title='Valid Title',
            title_color='#00FF00',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Fetch user meta
        response = authenticated_client.get('/api/users/me/meta/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['active_title'] == 'Valid Title'
        assert response.data['title_color'] == '#00FF00'

