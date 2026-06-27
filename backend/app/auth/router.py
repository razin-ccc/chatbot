from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth import handler
from auth.cookies import (
    REFRESH_TOKEN_COOKIE,
    clear_auth_cookies,
    set_auth_cookies,
)
from auth.model import Token
from auth.service import (
    authenticate_user,
    create_refresh_session,
    get_current_active_user,
    logout_service,
    prune_user_sessions,
    revoke_refresh_cookie_session,
    rotate_refresh_token,
)
from core.config import getSettings
from core.database import get_db
from core.errors import (
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
    UnknownError,
)
from schemas.models import User
from schemas.schema import UserCreate, UserMeResponse, UserResponse
from services.user import create_user_service, get_user_by_email

auth_router = APIRouter(prefix="/auth")


def _resolve_refresh_token(request: Request) -> str:
    token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not token:
        raise UnauthorizedError("Refresh token is required")
    return token


def _token_response(
    access_token: str, refresh_token: str | None = None
) -> JSONResponse:
    payload = Token(access_token=access_token, token_type="bearer")
    response = JSONResponse(content=payload.model_dump(exclude_none=True))
    if refresh_token:
        set_auth_cookies(response, refresh_token)
    return response


def _clear_session_response() -> JSONResponse:
    response = JSONResponse(content={"message": "Session cleared"})
    clear_auth_cookies(response)
    return response


@auth_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        permissions=sorted(current_user.permissions),
    )


@auth_router.post("/clear-session", status_code=status.HTTP_200_OK)
async def clear_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Clear auth cookies and revoke the refresh session without requiring an access token."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    response = _clear_session_response()

    try:
        await revoke_refresh_cookie_session(db, refresh_token)
    except Exception:
        await db.rollback()

    return response


@auth_router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register_user(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    settings = getSettings()
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise ForbiddenError("Registration is currently disabled")

    return await create_user_service(db, user)


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise UnauthorizedError("Incorrect email or password")

    settings = getSettings()
    await prune_user_sessions(db, user.id, settings.MAX_REFRESH_SESSIONS_PER_USER)

    user_scopes = list(user.permissions)
    access_token = handler.create_access_token(user.email, scopes=user_scopes)
    refresh_token = handler.create_refresh_token(user.email, scopes=user_scopes)
    await create_refresh_session(db, user, refresh_token)

    return _token_response(access_token, refresh_token)


@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = _resolve_refresh_token(request)
    new_access_token, new_refresh_token = await rotate_refresh_token(db, refresh_token)
    return _token_response(new_access_token, new_refresh_token)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke a refresh session. Requires a valid access token."""
    response = _clear_session_response()
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not refresh_token:
        return response

    try:
        # logout_service loads the session, verifies ownership, and deletes it.
        await logout_service(db, refresh_token, current_user)
    except UnauthorizedError:
        pass
    except Exception as e:
        raise UnknownError(f"Logout failed: {e}") from e

    return response
