"""
Tests for submission creation and comment toggle.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from submissions.models import Submission

User = get_user_model()


@pytest.mark.django_db
class TestSubmissionCreateAndToggleComment:
    """Test submission creation and comment toggle."""
    
    def test_create_submission(self, authenticated_client, user):
        """Test creating a submission."""
        response = authenticated_client.post('/api/submissions/', {
            'caption': 'Test submission',
            'comment_enabled': True
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['caption'] == 'Test submission'
        assert response.data['comment_enabled'] is True
        assert response.data['author'] == user.id
        
        # Verify in database
        submission = Submission.objects.get(id=response.data['id'])
        assert submission.author == user
        assert submission.caption == 'Test submission'
    
    def test_create_submission_with_image(self, authenticated_client, user):
        """Test creating a submission with image."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        image = SimpleUploadedFile(
            name='test.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        response = authenticated_client.post('/api/submissions/', {
            'image': image,
            'caption': 'Test with image',
            'comment_enabled': True
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'image' in response.data
    
    def test_toggle_comment_enabled(self, authenticated_client, submission):
        """Test toggling comment enabled by owner."""
        assert submission.comment_enabled is True
        
        response = authenticated_client.post(
            f'/api/submissions/{submission.id}/comments/toggle/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['comment_enabled'] is False
        
        # Verify in database
        submission.refresh_from_db()
        assert submission.comment_enabled is False
    
    def test_toggle_comment_not_owner(self, authenticated_client, submission):
        """Test toggling comment by non-owner fails."""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            display_id='otheruser'
        )
        authenticated_client.force_authenticate(user=other_user)
        
        response = authenticated_client.post(
            f'/api/submissions/{submission.id}/comments/toggle/'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_submissions_feed(self, authenticated_client, submission):
        """Test getting submissions feed."""
        response = authenticated_client.get('/api/submissions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_get_today_submissions(self, authenticated_client, submission):
        """Test getting today's submissions."""
        response = authenticated_client.get('/api/submissions/?day=today')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

