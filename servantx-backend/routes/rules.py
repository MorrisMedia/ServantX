from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from routes.auth import get_current_user
from services.contract_service import get_all_contracts, get_contract
from services.contract_rules_engine import build_rules_for_contract


router = APIRouter(prefix="/rules", tags=["rules"])


async def _load_contracts_for_hospital(hospital_id: str, contract_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if contract_id:
        contract = await get_contract(contract_id)
        if not contract:
            return []
        if contract.get("hospitalId") != hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this contract",
            )
        return [contract]

    return await get_all_contracts(hospital_id=hospital_id)


@router.get("")
async def get_rules(
    contract_id: Optional[str] = Query(None, alias="contractId"),
    rule_types: Optional[List[str]] = Query(None, alias="type"),
    is_active: Optional[bool] = Query(None, alias="isActive"),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate rules from contract text for the current hospital.
    Includes synthetic contracts because they are stored like normal contracts.
    """
    try:
        hospital_id = current_user["hospital_id"]
        contracts = await _load_contracts_for_hospital(hospital_id, contract_id)

        rules: List[Dict[str, Any]] = []
        for contract in contracts:
            rules.extend(build_rules_for_contract(contract))

        if rule_types:
            allowed = {rule_type.lower() for rule_type in rule_types}
            rules = [rule for rule in rules if rule.get("type", "").lower() in allowed]

        if is_active is not None:
            rules = [rule for rule in rules if bool(rule.get("isActive")) == is_active]

        return rules

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rules: {str(e)}",
        )


@router.get("/{rule_id}")
async def get_rule_by_id(rule_id: str, current_user: dict = Depends(get_current_user)):
    """
    Fetch one generated rule by ID.
    """
    try:
        hospital_id = current_user["hospital_id"]
        contracts = await _load_contracts_for_hospital(hospital_id)

        for contract in contracts:
            for rule in build_rules_for_contract(contract):
                if rule["id"] == rule_id:
                    return rule

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rule: {str(e)}",
        )
