"""
Tests for admin soft delete and restore submission.
"""
import pytest
from django.utils import timezone
from rest_framework import status
from submissions.models import Submission
from adminpanel.models import AdminAuditLog


@pytest.mark.django_db
class TestAdminSoftDeleteAndRestoreSubmission:
    """Test admin soft delete and restore submission."""
    
    def test_soft_delete_submission(self, admin_client, submission):
        """Test soft deleting a submission."""
        assert submission.deleted_at is None
        
        response = admin_client.post(
            f'/api/admin/submissions/{submission.id}/delete/',
            {'reason': 'Test deletion reason'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        submission.refresh_from_db()
        assert submission.deleted_at is not None
        assert submission.delete_reason == 'Test deletion reason'
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_submission=submission,
            action=AdminAuditLog.Action.DELETE
        ).first()
        assert log is not None
        assert log.payload.get('reason') == 'Test deletion reason'
    
    def test_restore_submission(self, admin_client, submission):
        """Test restoring a soft-deleted submission."""
        # First delete
        submission.soft_delete(reason='Test deletion')
        
        # Restore
        response = admin_client.post(
            f'/api/admin/submissions/{submission.id}/restore/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        submission.refresh_from_db()
        assert submission.deleted_at is None
        assert submission.delete_reason is None
        
        # Verify audit log
        log = AdminAuditLog.objects.filter(
            target_submission=submission,
            action=AdminAuditLog.Action.RESTORE
        ).first()
        assert log is not None
    
    def test_list_submissions_includes_deleted(self, admin_client, submission):
        """Test listing submissions includes deleted ones."""
        # Delete submission
        submission.soft_delete(reason='Test')
        
        # List with include_deleted
        response = admin_client.get('/api/admin/submissions/?include_deleted=true')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
        # Find deleted submission
        deleted = next(
            (s for s in response.data['results'] if s['id'] == submission.id),
            None
        )
        assert deleted is not None
        assert deleted['deleted_at'] is not None
    
    def test_list_submissions_excludes_deleted_by_default(self, admin_client, submission):
        """Test listing submissions excludes deleted by default."""
        # Delete submission
        submission.soft_delete(reason='Test')
        
        # List without include_deleted
        response = admin_client.get('/api/admin/submissions/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify deleted submission is not in results
        deleted = next(
            (s for s in response.data['results'] if s['id'] == submission.id),
            None
        )
        assert deleted is None
    
    def test_non_admin_cannot_delete(self, authenticated_client, submission):
        """Test that non-admin cannot delete submissions."""
        response = authenticated_client.post(
            f'/api/admin/submissions/{submission.id}/delete/',
            {'reason': 'Test'}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

