from datetime import datetime
from typing import Optional, Dict, Any
from models import AppAuditLog
from core_services.db_service import AsyncSessionLocal


async def log_event(
    event_type: str,
    hospital_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire-and-forget audit event. Never raises."""
    try:
        async with AsyncSessionLocal() as db:
            entry = AppAuditLog(
                hospital_id=hospital_id,
                user_id=user_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                metadata_json=metadata,
            )
            db.add(entry)
            await db.commit()
    except Exception:
        pass  # Never let audit logging crash the request
