import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings

# JWT Secret and Cryptographic Configuration
# In production, this is loaded from a secure vault or environment variable.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "chronis-secure-jwt-secret-key-2026-sde-evaluation")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hour token lifespan


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC with SHA-256 and a random 16-byte salt.
    We use 100,000 iterations to adhere to modern NIST password guidelines while
    avoiding external C-extension binary build dependencies (like bcrypt) on Windows/ARM.
    
    Returns a string in the format: "<salt_hex>:<hash_hex>".
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against the stored "<salt>:<hash>" string.
    Uses hmac.compare_digest for constant-time comparison to protect against
    side-channel timing attacks.
    """
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates and cryptographically signs a JWT access token containing the user's ID and email.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates the signature and expiration timestamp of a JWT token.
    Returns the decoded payload dict if valid, or None if expired/tampered.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
