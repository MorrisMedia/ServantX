"""
Authentication routes for login, register, and user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime
from sqlalchemy import delete, select
from schemas import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    User,
    UpdateHasContractRequest,
)
from config import settings
from core_services.db_service import AsyncSessionLocal
from models import (
    AuditFinding,
    AuditNote,
    BatchRun,
    Contract,
    Document,
    FormalAuditRun,
    ParsedData,
    Project,
    ProjectArtifact,
    Receipt,
    TruthVerificationRun,
)
from core_services.auth_service import (
    get_password_hash as hash_password,
    verify_password
)
from services.auth_service import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_from_token
)
from services.user_service import (
    create_user,
    get_user_by_email,
    get_user,
    verify_user_password,
    update_user,
)
from services.hospital_service import (
    create_hospital,
    get_hospital,
    update_hospital_config,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 scheme for Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """Dependency to get current authenticated user from Bearer token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = get_current_user_from_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    user = await get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:


    
        
        # Check if user already exists
        existing_user = await get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Create hospital
        hospital = await create_hospital(
            name=request.hospital_name,
            phone=request.phone,
        )
        
        # Create user
        try:
            password_hash = hash_password(request.password)
        except Exception as e:
            print(f"Error hashing password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing password",
            )
        
        user = await create_user(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
            hospital_id=hospital["id"],
            role="user",
        )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]}
        )
        refresh_token = create_refresh_token(
            data={"sub": user["id"], "email": user["email"]}
        )
        
        # Parse datetime string to datetime object
        created_at = datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
        
        return AuthResponse(
            user=User(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                hospital_id=user["hospital_id"],
                hospital_name=hospital["name"],
                role=user["role"],
                has_contract=user.get("has_contract", False),
                created_at=created_at,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            message="Registration successful",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:


        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password using JSON body"""
    # Check if user exists
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if password_hash exists
    if not user.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User account error",
        )
    
    # Verify password
    try:
        password_valid = verify_password(request.password, user["password_hash"])
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error for debugging but don't expose it to the user
        print(f"Password verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get hospital info
    hospital = await get_hospital(user["hospital_id"])
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]}
    )
    refresh_token = create_refresh_token(
        data={"sub": user["id"], "email": user["email"]}
    )
    
    # Parse datetime string to datetime object
    created_at = datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
    
    return AuthResponse(
        user=User(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            hospital_id=user["hospital_id"],
            hospital_name=hospital["name"] if hospital else None,
            role=user["role"],
            has_contract=user.get("has_contract", False),
            created_at=created_at,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    hospital = await get_hospital(current_user["hospital_id"])
    # Parse datetime string to datetime object
    created_at = datetime.fromisoformat(current_user["created_at"]) if isinstance(current_user["created_at"], str) else current_user["created_at"]
    
    return User(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        hospital_id=current_user["hospital_id"],
        hospital_name=hospital["name"] if hospital else None,
        role=current_user["role"],
        has_contract=current_user.get("has_contract", False),
        created_at=created_at,
    )


@router.post("/refresh")
async def refresh_token(request: dict):
    """Refresh access token using refresh token"""
    refresh_token_value = request.get("refresh_token") or request.get("refreshToken")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )
    
    payload = verify_token(refresh_token_value, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = await get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]}
    )
    
    return {
        "access_token": access_token,
        "accessToken": access_token,  # Support both formats
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout - invalidate token (client-side token removal is sufficient for JWT)"""
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(request: dict):
    """Send password reset email"""
    # TODO: Implement password reset email sending
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )
    
    user = await get_user_by_email(email)
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # TODO: Generate reset token and send email
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: dict):
    """Reset password with token"""
    # TODO: Implement password reset with token
    token = request.get("token")
    new_password = request.get("new_password") or request.get("newPassword")
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required",
        )
    
    # TODO: Verify token and update password
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset is not yet implemented",
    )


@router.post("/change-password")
async def change_password(request: dict, current_user: dict = Depends(get_current_user)):
    """Change password for authenticated user"""
    current_password = request.get("current_password") or request.get("currentPassword")
    new_password = request.get("new_password") or request.get("newPassword")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required",
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )
    
    # Verify current password
    if not verify_password(current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    
    # Update password
    new_password_hash = hash_password(new_password)
    await update_user(current_user["id"], password_hash=new_password_hash)
    
    return {"message": "Password changed successfully"}


@router.patch("/update-has-contract", response_model=User)
async def update_has_contract(
    request: UpdateHasContractRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update has_contract field for current user (temporary endpoint for testing)"""
    updated_user = await update_user(current_user["id"], has_contract=request.has_contract)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    hospital = await get_hospital(updated_user["hospital_id"])
    created_at = datetime.fromisoformat(updated_user["created_at"]) if isinstance(updated_user["created_at"], str) else updated_user["created_at"]
    
    return User(
        id=updated_user["id"],
        email=updated_user["email"],
        name=updated_user["name"],
        hospital_id=updated_user["hospital_id"],
        hospital_name=hospital["name"] if hospital else None,
        role=updated_user["role"],
        has_contract=updated_user.get("has_contract", False),
        created_at=created_at,
    )


VALID_PRICING_MODES = {"AUTO", "MEDICARE", "MEDICAID", "CONTRACT", "ALL"}


@router.get("/hospital/config")
async def get_hospital_config(current_user: dict = Depends(get_current_user)):
    """Get pricing configuration for the current user's hospital."""
    hospital = await get_hospital(current_user["hospital_id"])
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )
    return {
        "hospital_id": hospital["id"],
        "pricing_mode": hospital.get("pricing_mode", "AUTO"),
        "state": hospital.get("state"),
    }


@router.patch("/hospital/config")
async def patch_hospital_config(
    request: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update pricing_mode and/or state for the current user's hospital.

    Body: {"pricing_mode": "ALL", "state": "TX"}
    Valid pricing_mode values: AUTO, MEDICARE, MEDICAID, CONTRACT, ALL
    """
    pricing_mode = request.get("pricing_mode")
    state = request.get("state")

    if pricing_mode is not None and pricing_mode not in VALID_PRICING_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pricing_mode '{pricing_mode}'. Valid values: {sorted(VALID_PRICING_MODES)}",
        )
    if state is not None and (not isinstance(state, str) or len(state) != 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="state must be a 2-letter string (e.g. 'TX')",
        )

    updated = await update_hospital_config(
        hospital_id=current_user["hospital_id"],
        pricing_mode=pricing_mode,
        state=state.upper() if state else None,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )
    return {
        "hospital_id": updated["id"],
        "pricing_mode": updated["pricing_mode"],
        "state": updated["state"],
    }


@router.post("/reset-demo-data")
async def reset_demo_data(current_user: dict = Depends(get_current_user)):
    """Clear hospital-scoped demo/smoke artifacts for the current authenticated tenant."""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset is disabled in production",
        )

    hospital_id = current_user["hospital_id"]

    async with AsyncSessionLocal() as db:
        result = {}
        hospital_documents = select(Document.id).where(Document.hospital_id == hospital_id)
        hospital_batches = select(BatchRun.id).where(BatchRun.hospital_id == hospital_id)
        hospital_projects = select(Project.id).where(Project.hospital_id == hospital_id)

        delete_plan = [
            (ProjectArtifact, delete(ProjectArtifact).where(ProjectArtifact.hospital_id == hospital_id), "projectArtifacts"),
            (FormalAuditRun, delete(FormalAuditRun).where(FormalAuditRun.hospital_id == hospital_id), "formalAuditRuns"),
            (TruthVerificationRun, delete(TruthVerificationRun).where(TruthVerificationRun.hospital_id == hospital_id), "truthVerificationRuns"),
            (AuditFinding, delete(AuditFinding).where(AuditFinding.document_id.in_(hospital_documents)), "auditFindings"),
            (AuditNote, delete(AuditNote).where((AuditNote.document_id.in_(hospital_documents)) | (AuditNote.batch_id.in_(hospital_batches))), "auditNotes"),
            (ParsedData, delete(ParsedData).where((ParsedData.document_id.in_(hospital_documents)) | (ParsedData.batch_id.in_(hospital_batches))), "parsedData"),
            (Document, delete(Document).where(Document.hospital_id == hospital_id), "documents"),
            (Receipt, delete(Receipt).where(Receipt.hospital_id == hospital_id), "receipts"),
            (BatchRun, delete(BatchRun).where(BatchRun.hospital_id == hospital_id), "batchRuns"),
            (Contract, delete(Contract).where(Contract.hospital_id == hospital_id), "contracts"),
            (Project, delete(Project).where(Project.hospital_id == hospital_id), "projects"),
        ]

        for _model, stmt, key in delete_plan:
            deleted = await db.execute(stmt)
            result[key] = deleted.rowcount or 0

        await db.commit()

    await update_user(current_user["id"], has_contract=False)

    return {
        "message": "Demo data cleared",
        "hospitalId": hospital_id,
        "deleted": result,
    }

