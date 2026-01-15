"""StudySphere SSO service helpers."""
from __future__ import annotations

import logging
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 5


class SSOServiceError(Exception):
    """Raised when StudySphere SSO API fails."""


def _get_setting(name: str) -> str:
    value = getattr(settings, name, "") or ""
    if not value:
        raise SSOServiceError(f"Missing setting: {name}")
    return value


def _get_optional_setting(name: str) -> str:
    return getattr(settings, name, "") or ""


def _get_api_base_url() -> str:
    return (_get_optional_setting("SSO_API_BASE_URL") or _get_optional_setting("SSO_HUB_BASE_URL")).rstrip("/")


def _get_web_base_url() -> str:
    return (_get_optional_setting("SSO_WEB_BASE_URL") or _get_optional_setting("SSO_HUB_BASE_URL")).rstrip("/")


def _post_json(endpoint: str, payload: Dict[str, Any], headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    base_url = _get_api_base_url()
    if not base_url:
        raise SSOServiceError("Missing setting: SSO_API_BASE_URL or SSO_HUB_BASE_URL")
    url = f"{base_url}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.exception("SSO API request failed: %s", exc)
        raise SSOServiceError("SSO API request failed") from exc

    if not response.ok:
        logger.warning("SSO API error %s: %s", response.status_code, response.text)
        raise SSOServiceError(f"SSO API error: {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        logger.exception("Invalid JSON response from SSO API: %s", exc)
        raise SSOServiceError("Invalid JSON response from SSO API") from exc


def verify_ticket(ticket: str) -> Dict[str, Any]:
    payload = {"ticket": ticket}
    response = _post_json("/api/sso/ticket/verify", payload)
    if not response.get("valid"):
        logger.info("SSO ticket invalid: %s", ticket)
        raise SSOServiceError("Invalid SSO ticket")
    data = response.get("data") or {}
    if not data.get("user_id") or not (data.get("username") or data.get("login_code")):
        raise SSOServiceError("Missing user data from SSO verify response")
    return data


def generate_ticket(target_system: str) -> str:
    token = _get_setting("SSO_SERVICE_TOKEN")
    source_system = _get_setting("SSO_SYSTEM_KEY")
    payload = {"target_system": target_system, "source_system": source_system}
    headers = {"Authorization": f"Bearer {token}"}
    response = _post_json("/api/sso/ticket/generate", payload, headers=headers)
    if not response.get("success"):
        raise SSOServiceError("Failed to generate SSO ticket")
    data = response.get("data") or {}
    ticket = data.get("ticket")
    if not ticket:
        raise SSOServiceError("Missing ticket in SSO generate response")
    return str(ticket)


def generate_ticket_by_logincode(login_code: str, target_system: str, context: str | None = None) -> str:
    source_system = _get_setting("SSO_SYSTEM_KEY")
    payload: Dict[str, Any] = {
        "login_code": login_code,
        "target_system": target_system,
        "source_system": source_system,
    }
    if context:
        payload["context"] = context
    response = _post_json("/api/sso/ticket/generate-by-logincode", payload)
    if not response.get("success"):
        raise SSOServiceError("Failed to generate SSO ticket (login_code)")
    data = response.get("data") or {}
    ticket = data.get("ticket")
    if not ticket:
        raise SSOServiceError("Missing ticket in SSO generate-by-logincode response")
    return str(ticket)


def build_sso_login_url(ticket: str) -> str:
    base_url = _get_web_base_url()
    if not base_url:
        raise SSOServiceError("Missing setting: SSO_WEB_BASE_URL or SSO_HUB_BASE_URL")
    return f"{base_url}/sso-login?ticket={ticket}"


def build_sso_dispatch_url(ticket: str, target_system: str) -> str:
    base_url = _get_web_base_url()
    if not base_url:
        raise SSOServiceError("Missing setting: SSO_WEB_BASE_URL or SSO_HUB_BASE_URL")
    return f"{base_url}/sso-dispatch?target={target_system}&ticket={ticket}"
