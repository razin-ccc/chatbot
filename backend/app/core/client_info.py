from fastapi import Request

from core.config import getSettings

_MAX_USER_AGENT_LENGTH = 255


def trusted_client_ip(request: Request) -> str | None:
    """
    Return the caller's IP only when it is safe to enforce limits on it.

    Behind nginx, request.client is the proxy, so every user would share one limit.
    X-Real-IP is set by nginx, and it is only safe when nginx is the sole way in.
    """
    if getSettings().TRUST_PROXY_HEADERS:
        return request.headers.get("X-Real-IP")
    return None


def client_ip_for_logging(request: Request) -> str | None:
    """Return the best available IP for display. Never use this for security decisions."""
    if ip := trusted_client_ip(request):
        return ip
    return request.client.host if request.client else None


def client_user_agent(request: Request) -> str | None:
    user_agent = request.headers.get("User-Agent")
    return user_agent[:_MAX_USER_AGENT_LENGTH] if user_agent else None
