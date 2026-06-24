from fastapi import Response

from auth import handler
from core.config import getSettings

REFRESH_TOKEN_COOKIE = "refresh_token"
SESSION_COOKIE = "has_session"
REFRESH_COOKIE_PATH = "/auth"


def _cookie_secure() -> bool:
    return getSettings().ENVIRONMENT != "local"


def _refresh_max_age() -> int:
    return int(handler.REFRESH_TOKEN_EXPIRE_DAYS.total_seconds())


def set_auth_cookies(response: Response, refresh_token: str) -> None:
    secure = _cookie_secure()
    max_age = _refresh_max_age()

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path=REFRESH_COOKIE_PATH,
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value="1",
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    secure = _cookie_secure()
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE,
        path=REFRESH_COOKIE_PATH,
        secure=secure,
        samesite="lax",
    )
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=secure,
        samesite="lax",
    )
