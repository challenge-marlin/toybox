"""
Pytest configuration and fixtures.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import UserMeta
from submissions.models import Submission
from lottery.models import LotteryRule, JackpotWin
from sharing.models import DiscordShare
from adminpanel.models import AdminAuditLog

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        display_id='testuser',
        role=User.Role.USER
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_user(
        email='admin@example.com',
        password='adminpass123',
        display_id='admin',
        role=User.Role.ADMIN,
        is_staff=True
    )


@pytest.fixture
def office_user(db):
    """Create a test office user."""
    return User.objects.create_user(
        email='office@example.com',
        password='officepass123',
        display_id='office',
        role=User.Role.OFFICE
    )


@pytest.fixture
def user_meta(db, user):
    """Create user meta for test user."""
    return UserMeta.objects.create(
        user=user,
        active_title='Test Title',
        title_color='#FF0000',
        expires_at=timezone.now() + timedelta(days=7)
    )


@pytest.fixture
def submission(db, user):
    """Create a test submission."""
    return Submission.objects.create(
        author=user,
        caption='Test submission',
        comment_enabled=True,
        status=Submission.Status.PUBLIC
    )


@pytest.fixture
def lottery_rule(db):
    """Create a test lottery rule."""
    return LotteryRule.objects.create(
        base_rate=0.008,
        per_submit_increment=0.002,
        max_rate=0.05,
        daily_cap=1,
        is_active=True
    )


@pytest.fixture
def api_client():
    """Create API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Create authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client

