from fastapi import Response

from auth import handler
from core.config import getSettings

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"


def _cookie_secure() -> bool:
    return getSettings().ENVIRONMENT != "local"


def _refresh_max_age() -> int:
    return int(handler.REFRESH_TOKEN_EXPIRE_DAYS.total_seconds())


def set_auth_cookies(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        max_age=_refresh_max_age(),
        path=REFRESH_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE,
        path=REFRESH_COOKIE_PATH,
        secure=_cookie_secure(),
        samesite="lax",
    )
