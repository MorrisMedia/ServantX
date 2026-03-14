"""
Authentication service for handling JWT tokens and password hashing
"""
import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes will be truncated.
    """
    # Bcrypt has a 72-byte limit, so we need to handle longer passwords
    # Convert to bytes and truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes will be truncated.
    """
    try:
        # Bcrypt has a 72-byte limit, so we need to handle longer passwords
        # Convert to bytes and truncate if necessary (same as in hash_password)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            plain_password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log error for debugging
        print(f"Error in verify_password: {e}")
        return False


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user_from_token(token: str) -> Optional[Dict]:
    """Get user data from access token"""
    payload = verify_token(token, "access")
    if payload:
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
        }
    return None

