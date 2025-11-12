"""
Tests for admin reset password and audit logging.
"""
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from adminpanel.models import AdminAuditLog

User = get_user_model()


@pytest.mark.django_db
class TestAdminResetPasswordLogsAudit:
    """Test admin reset password and audit logging."""
    
    def test_reset_password(self, admin_client, user):
        """Test resetting user password."""
        old_password_hash = user.password
        
        response = admin_client.post(f'/api/admin/users/{user.id}/reset_password/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'temp_password' in response.data
        
        # Verify password changed
        user.refresh_from_db()
        assert user.password != old_password_hash
        
        # Verify new password works
        assert user.check_password(response.data['temp_password'])
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.RESET_PASSWORD
        ).first()
        assert log is not None
        assert log.actor == admin_user
        assert 'temp_password' in log.payload
    
    def test_reset_password_logs_audit(self, admin_client, user, admin_user):
        """Test that password reset is logged in audit."""
        response = admin_client.post(f'/api/admin/users/{user.id}/reset_password/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.RESET_PASSWORD
        ).first()
        
        assert log is not None
        assert log.actor == admin_user
        assert log.target_user == user
        assert log.action == AdminAuditLog.Action.RESET_PASSWORD
        assert 'temp_password' in log.payload
    
    def test_non_admin_cannot_reset_password(self, authenticated_client, user):
        """Test that non-admin cannot reset password."""
        response = authenticated_client.post(f'/api/admin/users/{user.id}/reset_password/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_reset_password_multiple_times(self, admin_client, user):
        """Test resetting password multiple times."""
        # First reset
        response1 = admin_client.post(f'/api/admin/users/{user.id}/reset_password/')
        assert response1.status_code == status.HTTP_200_OK
        password1 = response1.data['temp_password']
        
        # Second reset
        response2 = admin_client.post(f'/api/admin/users/{user.id}/reset_password/')
        assert response2.status_code == status.HTTP_200_OK
        password2 = response2.data['temp_password']
        
        # Verify passwords are different
        assert password1 != password2
        
        # Verify latest password works
        user.refresh_from_db()
        assert user.check_password(password2)
        
        # Verify audit logs
        logs = AdminAuditLog.objects.filter(
            target_user=user,
            action=AdminAuditLog.Action.RESET_PASSWORD
        )
        assert logs.count() == 2

