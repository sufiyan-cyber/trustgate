"""Security utilities: hashing, normalization, and JWT authentication."""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def normalize_id_number(raw_id: str) -> str:
    """Normalizes an ID number by stripping whitespace and uppercase conversion."""
    if not raw_id:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", raw_id).upper()

def hash_id_number(raw_id: str) -> str:
    """Computes SHA-256 hash of normalized ID for safe persistence and duplicate checks."""
    normalized = normalize_id_number(raw_id)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def normalize_name(name: str) -> str:
    """Normalizes participant name for fuzzy comparison."""
    if not name:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z\s]", "", name).strip()).upper()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
