from typing import Optional
from sqlalchemy import select
from models import User
from core_services.db_service import AsyncSessionLocal
from core_services.auth_service import verify_password

async def create_user(
    email: str,
    password_hash: str,
    name: str,
    hospital_id: str,
    role: str = "user",
    has_contract: bool = False
) -> dict:
    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            hospital_id=hospital_id,
            role=role,
            has_contract=has_contract
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "name": user.name,
            "hospital_id": user.hospital_id,
            "role": user.role,
            "has_contract": user.has_contract,
            "created_at": user.created_at.isoformat(),
        }

async def get_user_by_email(email: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == email.lower()))
        user = result.scalar_one_or_none()
        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "name": user.name,
            "hospital_id": user.hospital_id,
            "role": user.role,
            "is_admin": user.is_admin,
            "has_contract": user.has_contract,
            "created_at": user.created_at.isoformat(),
        }

async def get_user(user_id: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        return {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "name": user.name,
            "hospital_id": user.hospital_id,
            "role": user.role,
            "is_admin": user.is_admin,
            "has_contract": user.has_contract,
            "created_at": user.created_at.isoformat(),
        }

async def verify_user_password(email: str, password: str) -> Optional[dict]:
    user = await get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None

async def update_user(user_id: str, **kwargs) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
        
        return {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "name": user.name,
            "hospital_id": user.hospital_id,
            "role": user.role,
            "has_contract": user.has_contract,
            "created_at": user.created_at.isoformat(),
        }
