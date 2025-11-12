"""
Tests for JWT authentication.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestJWTAuth:
    """Test JWT authentication endpoints."""
    
    def test_login_success(self, api_client, user):
        """Test successful login."""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, api_client, user):
        """Test token refresh."""
        # First login
        login_response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        refresh_token = login_response.data['refresh']
        
        # Refresh token
        response = api_client.post('/api/auth/refresh/', {
            'refresh': refresh_token
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_protected_endpoint_without_auth(self, api_client):
        """Test accessing protected endpoint without authentication."""
        response = api_client.get('/api/users/me/meta/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_auth(self, authenticated_client):
        """Test accessing protected endpoint with authentication."""
        response = authenticated_client.get('/api/users/me/meta/')
        
        assert response.status_code == status.HTTP_200_OK

