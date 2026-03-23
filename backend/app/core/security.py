"""Security and authentication utilities"""
from datetime import datetime, timedelta
from typing import Optional
import base64
import hashlib
import hmac
import json
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed access token with expiry information."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode["exp"] = int(expire.timestamp())

    payload = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload).rstrip(b"=")

    secret = (settings.POSTGRES_PASSWORD or "stockinator-dev-secret").encode("utf-8")
    signature = hmac.new(secret, payload_b64, hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")

    return f"{payload_b64.decode('utf-8')}.{signature_b64.decode('utf-8')}"
