from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models import User, OAuthToken
from schemas import UserCreate, UserLogin, TokenResponse
from .logger_service import error_log
from passlib.context import CryptContext

from .db_service import get_db

oauth_scheme = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    if not username:
        return None
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    username: Optional[str] = None,
    name: Optional[str] = None,
    role: str = "user"
) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    
    user_data = {
        "email": email,
        "password": hashed_password,
        "name": name,
        "role": role,
        "is_active": True
    }
    
    if username is not None:
        user_data["username"] = username
    
    new_user = User(**user_data)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def create_oauth_token(
    db: AsyncSession,
    user_id: int,
    expires_in: int = 604800,  # Default 1 week (7 days)
    include_refresh: bool = True
) -> OAuthToken:
    """Create an OAuth token for a user"""
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32) if include_refresh else None
    
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    oauth_token = OAuthToken(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at
    )
    
    db.add(oauth_token)
    await db.commit()
    await db.refresh(oauth_token)
    return oauth_token


async def get_user_by_token(db: AsyncSession, token: str) -> Optional[User]:
    """Get user by access token"""
    result = await db.execute(
        select(User).join(OAuthToken).where(
            and_(
                OAuthToken.access_token == token,
                OAuthToken.revoked_at.is_(None),
                OAuthToken.expires_at > datetime.utcnow()
            )
        )
    )
    return result.scalar_one_or_none()


async def revoke_token(db: AsyncSession, token: str) -> bool:
    """Revoke an access token"""
    result = await db.execute(
        select(OAuthToken).where(
            and_(
                OAuthToken.access_token == token,
                OAuthToken.revoked_at.is_(None)
            )
        )
    )
    oauth_token = result.scalar_one_or_none()
    
    if oauth_token:
        oauth_token.revoked_at = datetime.utcnow()
        await db.commit()
        return True
    return False


async def revoke_user_tokens(db: AsyncSession, user_id: int) -> None:
    """Revoke all tokens for a user"""
    result = await db.execute(
        select(OAuthToken).where(
            and_(
                OAuthToken.user_id == user_id,
                OAuthToken.revoked_at.is_(None)
            )
        )
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked_at = datetime.utcnow()
    
    await db.commit()


def _generate_reset_code() -> str:
    """Generate a 6-digit reset code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


async def _set_password_reset_code(
    db: AsyncSession,
    user: User,
    expires_in: int = 600  # 10 minutes default
) -> str:
    """Set password reset code for user"""
    reset_code = _generate_reset_code()
    user.reset_password_code = reset_code
    user.reset_password_expires = datetime.utcnow() + timedelta(seconds=expires_in)
    
    await db.commit()
    return reset_code


async def _get_user_by_reset_code(
    db: AsyncSession,
    code: str,
    email: str
) -> Optional[User]:
    """Get user by reset code and email"""
    result = await db.execute(
        select(User).where(
            and_(
                User.email == email,
                User.reset_password_code == code,
                User.reset_password_expires > datetime.utcnow()
            )
        )
    )
    return result.scalar_one_or_none()


async def _clear_reset_token(db: AsyncSession, user: User) -> None:
    """Clear password reset code"""
    user.reset_password_code = None
    user.reset_password_expires = None
    await db.commit()


async def update_user_password(
    db: AsyncSession,
    user: User,
    new_password: str
) -> None:
    """Update user password and clear reset code"""
    user.password = get_password_hash(new_password)
    user.reset_password_code = None
    user.reset_password_expires = None
    await db.commit()


async def register_user(db: AsyncSession, user_data: UserCreate) -> tuple[User, TokenResponse]:
    existing_user = await _get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        name=user_data.name
    )
    
    token = await create_oauth_token(db, user.id)
    
    token_response = TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at
    )
    
    return user, token_response


async def login_user(db: AsyncSession, login_data: UserLogin) -> tuple[User, TokenResponse]:
    user = await _get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    token = await create_oauth_token(db, user.id)
    
    token_response = TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at
    )
    
    return user, token_response


async def logout_user(db: AsyncSession, token: str) -> None:
    revoked = await revoke_token(db, token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found or already revoked"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    user = await get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    result = await db.execute(select(User).filter(User.email == current_user.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user

