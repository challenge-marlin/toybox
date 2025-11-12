"""
Tests for admin warn, suspend, ban, and unban actions.
"""
import pytest
from django.utils import timezone
from rest_framework import status
from adminpanel.models import AdminAuditLog


@pytest.mark.django_db
class TestAdminWarnSuspendBanUnban:
    """Test admin warn, suspend, ban, and unban actions."""
    
    def test_warn_user(self, admin_client, user):
        """Test warning a user."""
        initial_count = user.warning_count
        
        response = admin_client.post(
            f'/api/admin/users/{user.id}/warn/',
            {'message': 'Test warning'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['warning_count'] == initial_count + 1
        
        # Verify in database
        user.refresh_from_db()
        assert user.warning_count == initial_count + 1
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.WARN
        ).first()
        assert log is not None
        assert log.actor == admin_client.handler._force_user
        assert 'Test warning' in log.payload.get('message', '')
    
    def test_suspend_user(self, admin_client, user):
        """Test suspending a user."""
        assert user.is_suspended is False
        
        response = admin_client.post(f'/api/admin/users/{user.id}/suspend/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        user.refresh_from_db()
        assert user.is_suspended is True
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.SUSPEND
        ).first()
        assert log is not None
    
    def test_unsuspend_user(self, admin_client, user):
        """Test unsuspending a user."""
        user.is_suspended = True
        user.save()
        
        response = admin_client.post(f'/api/admin/users/{user.id}/unsuspend/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        user.refresh_from_db()
        assert user.is_suspended is False
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.UNSUSPEND
        ).first()
        assert log is not None
    
    def test_ban_user(self, admin_client, user):
        """Test banning a user."""
        assert user.banned_at is None
        
        response = admin_client.post(f'/api/admin/users/{user.id}/ban/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        user.refresh_from_db()
        assert user.banned_at is not None
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.BAN
        ).first()
        assert log is not None
    
    def test_unban_user(self, admin_client, user):
        """Test unbanning a user."""
        user.banned_at = timezone.now()
        user.save()
        
        response = admin_client.post(f'/api/admin/users/{user.id}/unban/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        user.refresh_from_db()
        assert user.banned_at is None
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.UNBAN
        ).first()
        assert log is not None
    
    def test_non_admin_cannot_warn(self, authenticated_client, user):
        """Test that non-admin cannot warn users."""
        response = authenticated_client.post(
            f'/api/admin/users/{user.id}/warn/',
            {'message': 'Test warning'}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

