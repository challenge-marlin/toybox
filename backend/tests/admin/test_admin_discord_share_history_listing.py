"""
Tests for admin Discord share history listing.
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from sharing.models import DiscordShare

User = get_user_model()


@pytest.mark.django_db
class TestAdminDiscordShareHistoryListing:
    """Test admin Discord share history listing."""
    
    def test_list_discord_shares(self, admin_client, user, submission):
        """Test listing Discord shares."""
        # Create Discord shares
        share1 = DiscordShare.objects.create(
            user=user,
            submission=submission,
            share_channel='general',
            message_id='123456789'
        )
        share2 = DiscordShare.objects.create(
            user=user,
            submission=None,
            share_channel='announcements',
            message_id='987654321'
        )
        
        response = admin_client.get('/api/admin/discord-shares/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
        
        # Verify shares are in results
        share_ids = [s['id'] for s in response.data['results']]
        assert share1.id in share_ids
        assert share2.id in share_ids
    
    def test_filter_discord_shares_by_user(self, admin_client, user, submission):
        """Test filtering Discord shares by user."""
        # Create shares for different users
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            display_id='otheruser'
        )
        
        share1 = DiscordShare.objects.create(
            user=user,
            submission=submission,
            share_channel='general'
        )
        share2 = DiscordShare.objects.create(
            user=other_user,
            submission=submission,
            share_channel='general'
        )
        
        response = admin_client.get(f'/api/admin/discord-shares/?user={user.id}')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify only user's shares are returned
        share_ids = [s['id'] for s in response.data['results']]
        assert share1.id in share_ids
        assert share2.id not in share_ids
    
    def test_filter_discord_shares_by_channel(self, admin_client, user, submission):
        """Test filtering Discord shares by channel."""
        share1 = DiscordShare.objects.create(
            user=user,
            submission=submission,
            share_channel='general'
        )
        share2 = DiscordShare.objects.create(
            user=user,
            submission=submission,
            share_channel='announcements'
        )
        
        response = admin_client.get('/api/admin/discord-shares/?share_channel=general')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify only general channel shares are returned
        share_ids = [s['id'] for s in response.data['results']]
        assert share1.id in share_ids
        assert share2.id not in share_ids
    
    def test_discord_share_serializer_includes_user_info(self, admin_client, user, submission):
        """Test that Discord share serializer includes user info."""
        share = DiscordShare.objects.create(
            user=user,
            submission=submission,
            share_channel='general',
            message_id='123456789'
        )
        
        response = admin_client.get(f'/api/admin/discord-shares/{share.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user_email' in response.data
        assert 'user_display_id' in response.data
        assert response.data['user_email'] == user.email
        assert response.data['user_display_id'] == user.display_id
    
    def test_non_admin_cannot_list_shares(self, authenticated_client):
        """Test that non-admin cannot list Discord shares."""
        response = authenticated_client.get('/api/admin/discord-shares/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

