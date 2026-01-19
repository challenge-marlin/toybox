"""Authentication backend for StudySphere SSO."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

logger = logging.getLogger(__name__)


class StudySphereBackend(BaseBackend):
    """Authenticate users using StudySphere SSO data."""

    def authenticate(self, request, sso_data: Optional[Dict[str, Any]] = None, **kwargs):
        if not sso_data:
            return None

        user_id = sso_data.get("user_id")
        username = sso_data.get("username") or sso_data.get("login_code")
        role_value = sso_data.get("role")

        if user_id is None or not username:
            logger.warning("SSO data missing user_id or username: %s", sso_data)
            return None

        User = get_user_model()

        user = User.objects.filter(studysphere_user_id=user_id).first()
        if not user:
            user = User.objects.filter(
                Q(studysphere_login_code=username) | Q(display_id=username)
            ).first()

        if not user:
            role = self._map_role(User, role_value)
            user = User.objects.create_user(
                email=None,
                password=None,
                display_id=username,
                role=role,
                studysphere_user_id=user_id,
                studysphere_login_code=username,
            )
            logger.info("Created user via SSO: %s (studysphere_id=%s)", username, user_id)
            return user

        updated = False
        if getattr(user, "studysphere_user_id", None) is None:
            user.studysphere_user_id = user_id
            updated = True
        if getattr(user, "studysphere_login_code", None) != username:
            user.studysphere_login_code = username
            updated = True

        # Upgrade role if StudySphere provides a higher role
        mapped_role = self._map_role(User, role_value)
        if mapped_role and getattr(user, "role", None) == User.Role.FREE_USER and mapped_role != user.role:
            user.role = mapped_role
            updated = True

        if updated:
            user.save(update_fields=["studysphere_user_id", "studysphere_login_code", "role"])

        logger.info("Authenticated user via SSO: %s (studysphere_id=%s)", user.display_id, user_id)
        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def _map_role(User, role_value) -> str:
        role_map = {
            1: User.Role.FREE_USER,   # Learner
            2: User.Role.PAID_USER,
            9: User.Role.ADMIN,
            99: User.Role.SUPERUSER,
        }
        try:
            return role_map.get(int(role_value), User.Role.FREE_USER)
        except (TypeError, ValueError):
            return User.Role.FREE_USER
