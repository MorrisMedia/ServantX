from typing import Optional
from sqlalchemy import select
from models import Hospital
from core_services.db_service import AsyncSessionLocal

async def create_hospital(name: str, phone: Optional[str] = None) -> dict:
    async with AsyncSessionLocal() as db:
        hospital = Hospital(
            name=name,
            phone=phone
        )
        db.add(hospital)
        await db.commit()
        await db.refresh(hospital)
        
        return {
            "id": hospital.id,
            "name": hospital.name,
            "phone": hospital.phone,
            "created_at": hospital.created_at.isoformat(),
        }

async def get_hospital(hospital_id: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Hospital).filter(Hospital.id == hospital_id))
        hospital = result.scalar_one_or_none()
        if not hospital:
            return None
        
        return {
            "id": hospital.id,
            "name": hospital.name,
            "phone": hospital.phone,
            "created_at": hospital.created_at.isoformat(),
        }
