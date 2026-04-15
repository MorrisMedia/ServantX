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
            "pricing_mode": hospital.pricing_mode,
            "state": hospital.state,
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
            "pricing_mode": hospital.pricing_mode if hospital.pricing_mode else "AUTO",
            "state": hospital.state,
            "created_at": hospital.created_at.isoformat(),
        }

async def update_hospital_config(
    hospital_id: str,
    pricing_mode: Optional[str] = None,
    state: Optional[str] = None,
) -> Optional[dict]:
    """Update pricing_mode and/or state for a hospital. Returns updated hospital dict."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Hospital).filter(Hospital.id == hospital_id))
        hospital = result.scalar_one_or_none()
        if not hospital:
            return None

        if pricing_mode is not None:
            hospital.pricing_mode = pricing_mode
        if state is not None:
            hospital.state = state

        await db.commit()
        await db.refresh(hospital)

        return {
            "id": hospital.id,
            "name": hospital.name,
            "phone": hospital.phone,
            "pricing_mode": hospital.pricing_mode,
            "state": hospital.state,
            "created_at": hospital.created_at.isoformat(),
        }
