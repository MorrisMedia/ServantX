from typing import List, Optional
from sqlalchemy import select
from models import Receipt
from core_services.db_service import AsyncSessionLocal
from sqlalchemy import func

async def create_receipt(
    hospital_id: str,
    file_name: str,
    file_path: str,
    file_size: int,
    amount: float = 0.0,
    has_difference: bool = False
) -> dict:
    async with AsyncSessionLocal() as db:
        receipt = Receipt(
            hospital_id=hospital_id,
            has_difference=has_difference,
            amount=amount,
            document_id=None,
            file_name=file_name,
            file_size=file_size,
            file_url=file_path,
            status="pending"
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        
        return {
            "id": receipt.id,
            "hospitalId": receipt.hospital_id,
            "hasDifference": receipt.has_difference,
            "amount": receipt.amount,
            "uploadedAt": receipt.uploaded_at,
            "documentId": receipt.document_id,
            "fileName": receipt.file_name,
            "fileSize": receipt.file_size,
            "fileUrl": receipt.file_url,
            "status": receipt.status
        }

async def get_receipt(receipt_id: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Receipt).filter(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if not receipt:
            return None
        
        return {
            "id": receipt.id,
            "hospitalId": receipt.hospital_id,
            "hasDifference": receipt.has_difference,
            "amount": receipt.amount,
            "uploadedAt": receipt.uploaded_at,
            "documentId": receipt.document_id,
            "fileName": receipt.file_name,
            "fileSize": receipt.file_size,
            "fileUrl": receipt.file_url,
            "status": receipt.status
        }

async def get_all_receipts(
    hospital_id: Optional[str] = None,
    has_difference: Optional[bool] = None,
    status: Optional[List[str]] = None,
    search: Optional[str] = None,
    limit: int = 15,
    offset: int = 0
) -> tuple[List[dict], int]:
    async with AsyncSessionLocal() as db:        
        query = select(Receipt)
        count_query = select(func.count(Receipt.id))
        
        if hospital_id:
            query = query.filter(Receipt.hospital_id == hospital_id)
            count_query = count_query.filter(Receipt.hospital_id == hospital_id)
        
        if has_difference is not None:
            query = query.filter(Receipt.has_difference == has_difference)
            count_query = count_query.filter(Receipt.has_difference == has_difference)
        
        if status:
            query = query.filter(Receipt.status.in_(status))
            count_query = count_query.filter(Receipt.status.in_(status))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(Receipt.file_name.ilike(search_pattern))
            count_query = count_query.filter(Receipt.file_name.ilike(search_pattern))
        
        query = query.order_by(Receipt.uploaded_at.desc())
        query = query.limit(limit).offset(offset)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        result = await db.execute(query)
        receipts = result.scalars().all()
        
        items = [
            {
                "id": receipt.id,
                "hospitalId": receipt.hospital_id,
                "hasDifference": receipt.has_difference,
                "amount": receipt.amount,
                "uploadedAt": receipt.uploaded_at,
                "documentId": receipt.document_id,
                "fileName": receipt.file_name,
                "fileSize": receipt.file_size,
                "fileUrl": receipt.file_url,
                "status": receipt.status
            }
            for receipt in receipts
        ]
        
        return items, total

async def get_all_receipts_for_hospital(hospital_id: str) -> List[dict]:
    """Return every receipt for a hospital (no pagination), used for bulk re-scan."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Receipt)
            .filter(Receipt.hospital_id == hospital_id)
            .order_by(Receipt.uploaded_at.asc())
        )
        receipts = result.scalars().all()
        return [
            {
                "id": receipt.id,
                "hospitalId": receipt.hospital_id,
                "hasDifference": receipt.has_difference,
                "amount": receipt.amount,
                "uploadedAt": receipt.uploaded_at,
                "documentId": receipt.document_id,
                "fileName": receipt.file_name,
                "fileSize": receipt.file_size,
                "fileUrl": receipt.file_url,
                "status": receipt.status,
            }
            for receipt in receipts
        ]


async def delete_receipt(receipt_id: str) -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Receipt).filter(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if not receipt:
            return False
        
        await db.delete(receipt)
        await db.commit()
        return True

async def update_receipt(receipt_id: str, **kwargs) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Receipt).filter(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if not receipt:
            return None
        
        for key, value in kwargs.items():
            snake_key = key
            if key == "hospitalId":
                snake_key = "hospital_id"
            elif key == "hasDifference":
                snake_key = "has_difference"
            elif key == "uploadedAt":
                snake_key = "uploaded_at"
            elif key == "documentId":
                snake_key = "document_id"
            elif key == "fileName":
                snake_key = "file_name"
            elif key == "fileSize":
                snake_key = "file_size"
            elif key == "fileUrl":
                snake_key = "file_url"
            
            if hasattr(receipt, snake_key):
                setattr(receipt, snake_key, value)
        
        await db.commit()
        await db.refresh(receipt)
        
        return {
            "id": receipt.id,
            "hospitalId": receipt.hospital_id,
            "hasDifference": receipt.has_difference,
            "amount": receipt.amount,
            "uploadedAt": receipt.uploaded_at,
            "documentId": receipt.document_id,
            "fileName": receipt.file_name,
            "fileSize": receipt.file_size,
            "fileUrl": receipt.file_url,
            "status": receipt.status
        }
