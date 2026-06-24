from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth import handler
from auth.model import TokenData
from auth.security import hash_token, verify_hash
from core.database import get_db
from core.errors import BadRequest, UnauthorizedError, ForbiddenError
from schemas.models import Session, User
from services.user import get_user_by_email
from fastapi.security import SecurityScopes
from fastapi import Security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _assert_active_user(user: User) -> None:
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_hash(password, user.password):
        return None
    if not user.is_active:
        return None
    return user


async def get_session_by_refresh_token(
    db: AsyncSession, refresh_token: str
) -> Session | None:
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(Session).where(Session.refresh_token == token_hash)
    )
    return result.scalar_one_or_none()


async def get_session_by_refresh_token_for_update(
    db: AsyncSession, refresh_token: str
) -> Session | None:
    """Load a refresh session row with a pessimistic lock for rotation."""
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(Session)
        .where(Session.refresh_token == token_hash)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def create_refresh_session(
    db: AsyncSession, user: User, refresh_token: str
) -> Session:
    expires_at = datetime.now(timezone.utc) + handler.REFRESH_TOKEN_EXPIRE_DAYS
    session = Session(
        user_id=user.id,
        refresh_token=hash_token(refresh_token),
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def prune_user_sessions(
    db: AsyncSession, user_id: UUID, max_sessions: int
) -> None:
    """Remove oldest refresh sessions so a new login stays within the cap."""
    if max_sessions <= 0:
        return

    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.asc())
    )
    sessions = list(result.scalars().all())
    excess = len(sessions) - max_sessions + 1
    if excess <= 0:
        return

    for session in sessions[:excess]:
        await db.delete(session)
    await db.flush()


async def verify_refresh_token_stored(db: AsyncSession, refresh_token: str) -> Session:
    session = await get_session_by_refresh_token(db, refresh_token)
    if session is None:
        raise UnauthorizedError("Refresh token has been revoked")

    if session.expires_at < datetime.now(timezone.utc):
        await db.delete(session)
        await db.commit()
        raise UnauthorizedError("Refresh token has expired")

    return session


async def verify_refresh_token(token: str, db: AsyncSession):
    try:
        payload = handler.decode(token)

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        email = payload.get("sub")
        if email is None:
            raise UnauthorizedError("Invalid token payload")

        user = await get_user_by_email(db, email=email)
        if user is None:
            raise UnauthorizedError("User not found")

        return user, payload
    except InvalidTokenError as e:
        raise UnauthorizedError("Invalid or expired refresh token") from e


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credential_exceptions = UnauthorizedError("Could not validate credentials")

    token_data = None
    try:
        payload = handler.decode(token)

        if payload.get("type") != "access":
            raise credential_exceptions

        email = payload.get("sub")
        if email is None:
            raise credential_exceptions

        token_data = TokenData(email=email)
        user = await get_user_by_email(db, email=token_data.email)
        if user is None:
            raise credential_exceptions

        live_permissions = user.permissions
        for scope in security_scopes.scopes:
            if scope not in live_permissions:
                raise ForbiddenError("Insufficient permissions")

    except InvalidTokenError as e:
        raise credential_exceptions from e

    return user


async def get_current_active_user(current_user: User = Security(get_current_user)):
    if not current_user.is_active:
        raise BadRequest("Inactive user")
    return current_user


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    """Validate the current refresh token, revoke it, and issue rotated tokens."""
    session = await get_session_by_refresh_token_for_update(db, refresh_token)
    if session is None:
        raise UnauthorizedError("Refresh token has been revoked")

    if session.expires_at < datetime.now(timezone.utc):
        await db.delete(session)
        await db.commit()
        raise UnauthorizedError("Refresh token has expired")

    user, _ = await verify_refresh_token(refresh_token, db)

    if session.user_id != user.id:
        raise UnauthorizedError("Refresh token does not belong to current user")

    _assert_active_user(user)

    fresh_scopes = list(user.permissions)
    new_access_token = handler.create_access_token(user.email, scopes=fresh_scopes)
    new_refresh_token = handler.create_refresh_token(user.email, scopes=fresh_scopes)
    expires_at = datetime.now(timezone.utc) + handler.REFRESH_TOKEN_EXPIRE_DAYS

    try:
        await db.delete(session)
        db.add(
            Session(
                user_id=user.id,
                refresh_token=hash_token(new_refresh_token),
                expires_at=expires_at,
            )
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return new_access_token, new_refresh_token


async def logout_service(db: AsyncSession, refresh_token: str, user: User) -> None:
    session = await get_session_by_refresh_token(db, refresh_token)
    if session is None:
        raise UnauthorizedError("Refresh token has been revoked")
    if session.user_id != user.id:
        raise UnauthorizedError("Refresh token does not belong to current user")
    await db.delete(session)
    await db.commit()


async def revoke_refresh_cookie_session(
    db: AsyncSession, refresh_token: str | None
) -> None:
    """Revoke a refresh session from the HttpOnly cookie when present."""
    if not refresh_token:
        return

    session = await get_session_by_refresh_token(db, refresh_token)
    if session is None:
        return

    await db.delete(session)
    await db.commit()
