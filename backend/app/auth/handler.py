from core.config import getSettings
from datetime import datetime, timedelta, timezone
import jwt
import secrets

settings = getSettings()
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE_DAYS = timedelta(days=7)


def create_access_token(email: str, scopes: list[str] | None = None):
    """Create a short-lived access token (15 minutes)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES,
        "type": "access",
        "scopes": scopes or [],
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(email: str, scopes: list[str] | None = None):
    """Create a long-lived refresh token (7 days)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + REFRESH_TOKEN_EXPIRE_DAYS,
        "type": "refresh",
        "scopes": scopes or [],
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode(token: str) -> dict:
    """Decode and verify a JWT. Raises Error if invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
