from core.config import getSettings
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
import secrets

settings = getSettings()
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE_DAYS = timedelta(days=7)


def _create_token(
    email: str, session_id: UUID, token_type: str, lifetime: timedelta
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "sid": str(session_id),
        "iat": now,
        "exp": now + lifetime,
        "type": token_type,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(email: str, session_id: UUID) -> str:
    """Create a short-lived access token tied to a session."""
    return _create_token(email, session_id, "access", ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(email: str, session_id: UUID) -> str:
    """Create a long-lived refresh token tied to a session."""
    return _create_token(email, session_id, "refresh", REFRESH_TOKEN_EXPIRE_DAYS)


def decode(token: str) -> dict:
    """Decode and verify a JWT. Raises Error if invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
