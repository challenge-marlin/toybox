"""
Tests for admin permissions.
"""
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAdminPermissions:
    """Test admin permissions."""
    
    def test_admin_can_access_admin_endpoints(self, admin_client, user):
        """Test that admin can access admin endpoints."""
        response = admin_client.get('/api/admin/users/')
        assert response.status_code == status.HTTP_200_OK
        
        response = admin_client.get(f'/api/admin/users/{user.id}/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_office_user_can_access_admin_endpoints(self, api_client, office_user):
        """Test that office user can access admin endpoints."""
        api_client.force_authenticate(user=office_user)
        
        response = api_client.get('/api/admin/users/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_ayatori_user_can_access_admin_endpoints(self, api_client):
        """Test that ayatori user can access admin endpoints."""
        ayatori_user = User.objects.create_user(
            email='ayatori@example.com',
            password='ayatoripass123',
            display_id='ayatori',
            role=User.Role.AYATORI
        )
        api_client.force_authenticate(user=ayatori_user)
        
        response = api_client.get('/api/admin/users/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_regular_user_cannot_access_admin_endpoints(self, authenticated_client):
        """Test that regular user cannot access admin endpoints."""
        response = authenticated_client.get('/api/admin/users/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_warn_user(self, admin_client, user):
        """Test that admin can warn user."""
        response = admin_client.post(
            f'/api/admin/users/{user.id}/warn/',
            {'message': 'Test warning'}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_office_user_can_warn_user(self, api_client, office_user, user):
        """Test that office user can warn user."""
        api_client.force_authenticate(user=office_user)
        
        response = api_client.post(
            f'/api/admin/users/{user.id}/warn/',
            {'message': 'Test warning'}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_regular_user_cannot_warn(self, authenticated_client, user):
        """Test that regular user cannot warn."""
        response = authenticated_client.post(
            f'/api/admin/users/{user.id}/warn/',
            {'message': 'Test warning'}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access_audit_logs(self, admin_client):
        """Test that admin can access audit logs."""
        response = admin_client.get('/api/admin/audit-logs/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_ayatori_can_access_audit_logs(self, api_client):
        """Test that ayatori can access audit logs."""
        ayatori_user = User.objects.create_user(
            email='ayatori@example.com',
            password='ayatoripass123',
            display_id='ayatori',
            role=User.Role.AYATORI
        )
        api_client.force_authenticate(user=ayatori_user)
        
        response = api_client.get('/api/admin/audit-logs/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_office_user_cannot_access_audit_logs(self, api_client, office_user):
        """Test that office user cannot access audit logs."""
        api_client.force_authenticate(user=office_user)
        
        response = api_client.get('/api/admin/audit-logs/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_regular_user_cannot_access_audit_logs(self, authenticated_client):
        """Test that regular user cannot access audit logs."""
        response = authenticated_client.get('/api/admin/audit-logs/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

