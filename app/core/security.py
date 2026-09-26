from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from app.core.config import SECRET_KEY

password_hash = PasswordHash.recommended()
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _get_secret_key() -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be configured")
    return SECRET_KEY


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        _get_secret_key(),
        algorithm="HS256",
    )


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, _get_secret_key(), algorithms=["HS256"])
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Token subject is invalid") from exc


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(password: str, hash: str):
    return password_hash.verify(password, hash)
