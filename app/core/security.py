import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Dict, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback if bcrypt hash format differs
        digest = hashlib.sha256((plain_password + settings.SECRET_KEY).encode()).hexdigest()
        return hmac.compare_digest(digest, hashed_password)

def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        return hashlib.sha256((password + settings.SECRET_KEY).encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_otp() -> str:
    """Generate 6-digit numeric OTP"""
    return f"{secrets.randbelow(900000) + 100000}"

def hash_otp(otp: str, user_id: str) -> str:
    return hashlib.sha256(f"{otp}:{user_id}:{settings.SECRET_KEY}".encode()).hexdigest()

def verify_otp_hash(otp: str, user_id: str, stored_hash: str) -> bool:
    expected = hash_otp(otp, user_id)
    return hmac.compare_digest(expected, stored_hash)
