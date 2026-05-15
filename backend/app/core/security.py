from __future__ import annotations
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: str, role: str, expire_hours: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours or settings.session_expire_hours)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def create_magic_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
