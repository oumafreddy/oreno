"""Shared login lockout helpers (AccountLockout + django-axes)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    if request is None:
        return '0.0.0.0'
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or '0.0.0.0'


def is_login_locked(user, request=None, ip_address: str | None = None) -> bool:
    """True if the user is locked by org policy or django-axes."""
    if user is None or not getattr(user, 'pk', None):
        return False

    from users.models import AccountLockout

    ip = ip_address or (get_client_ip(request) if request else None)
    if AccountLockout.is_user_locked(user, ip_address=ip):
        return True

    try:
        from axes.handlers.proxy import AxesProxyHandler

        username = getattr(user, 'get_username', lambda: None)() or getattr(user, 'email', None)
        if not username:
            return False

        credentials = {'username': username}
        if request is not None and AxesProxyHandler.is_locked(request, credentials):
            return True
    except Exception as exc:
        logger.debug("axes lockout check skipped: %s", exc)

    return False


def record_login_failure(user, request=None, ip_address: str | None = None, user_agent: str = '') -> None:
    """Record failed login in AccountLockout for audit dashboards."""
    if user is None:
        return
    from users.models import AccountLockout

    ip = ip_address or get_client_ip(request)
    AccountLockout.record_failed_attempt(user, ip, user_agent or '')


def reset_login_lockout(user, request=None) -> None:
    """Clear django-axes and org lockout state after successful authentication."""
    if user is None:
        return

    from users.models import AccountLockout

    AccountLockout.objects.filter(user=user, is_active=True).update(is_active=False)

    try:
        from axes.utils import reset

        username = getattr(user, 'get_username', lambda: None)() or getattr(user, 'email', None)
        if username:
            reset(username=username)
        if request is not None:
            from axes.utils import reset_request
            reset_request(request, username=username)
    except Exception as exc:
        logger.debug("axes reset skipped: %s", exc)
