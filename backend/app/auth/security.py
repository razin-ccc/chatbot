import hashlib

from bcrypt import checkpw, gensalt, hashpw


def get_hash(text: str) -> str:
    """Generates hash of plain text"""
    return hashpw(text.encode("utf-8"), gensalt()).decode("utf-8")


def verify_hash(plain_text: str, hashed_text: str) -> bool:
    """Verifies plain text with hashed text"""
    try:
        return checkpw(plain_text.encode("utf-8"), hashed_text.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    """Hash a JWT refresh token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
