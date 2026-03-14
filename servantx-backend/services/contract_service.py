from typing import List, Optional
from sqlalchemy import select
from models import Contract
from core_services.db_service import AsyncSessionLocal
from models import Document


async def create_contract(
    hospital_id: str,
    name: str,
    file_name: str,
    file_path: str,
    file_size: int
) -> dict:
    async with AsyncSessionLocal() as db:
        contract = Contract(
            hospital_id=hospital_id,
            name=name,
            file_name=file_name,
            file_size=file_size,
            file_url=file_path,
            status="processing",
            rules_extracted=None,
            notes=None
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        
        return _contract_to_dict(contract)


def _contract_to_dict(contract) -> dict:
    """Convert a Contract ORM instance to a serializable dict."""
    return {
        "id": contract.id,
        "hospitalId": contract.hospital_id,
        "name": contract.name,
        "fileName": contract.file_name,
        "fileSize": contract.file_size,
        "fileUrl": contract.file_url,
        "uploadedAt": contract.uploaded_at,
        "status": contract.status,
        "rulesExtracted": contract.rules_extracted,
        "notes": contract.notes,
        "ruleLibrary": contract.rule_library,
    }


async def get_contract(contract_id: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Contract).filter(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return None
        
        return _contract_to_dict(contract)

async def get_all_contracts(hospital_id: Optional[str] = None) -> List[dict]:
    async with AsyncSessionLocal() as db:
        query = select(Contract)
        if hospital_id:
            query = query.filter(Contract.hospital_id == hospital_id)
        
        result = await db.execute(query)
        contracts = result.scalars().all()
        
        return [_contract_to_dict(contract) for contract in contracts]

async def delete_contract(contract_id: str) -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Contract).filter(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return False
        
        doc_result = await db.execute(select(Document).filter(Document.contract_id == contract_id))
        documents = doc_result.scalars().all()
        for doc in documents:
            doc.contract_id = None
        
        await db.delete(contract)
        await db.commit()
        return True

async def update_contract(contract_id: str, **kwargs) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Contract).filter(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return None
        
        for key, value in kwargs.items():
            snake_key = key
            if key == "hospitalId":
                snake_key = "hospital_id"
            elif key == "fileName":
                snake_key = "file_name"
            elif key == "fileSize":
                snake_key = "file_size"
            elif key == "fileUrl":
                snake_key = "file_url"
            elif key == "uploadedAt":
                snake_key = "uploaded_at"
            elif key == "rulesExtracted":
                snake_key = "rules_extracted"
            elif key == "ruleLibrary":
                snake_key = "rule_library"
            
            if hasattr(contract, snake_key):
                setattr(contract, snake_key, value)
        
        await db.commit()
        await db.refresh(contract)
        
        return _contract_to_dict(contract)
