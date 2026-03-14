from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import FormalAuditRun, Project, TruthVerificationRun
from routes.auth import get_current_user
from schemas import (
    FormalAuditRunCreateRequest,
    FormalAuditRunResponse,
    ProjectCreateRequest,
    ProjectResponse,
    StoragePresignRequest,
    StoragePresignResponse,
    TruthVerificationRequest,
    TruthVerificationResponse,
)
from services.formal_audit_service import create_formal_audit_run
from services.project_service import create_project_for_hospital, ensure_default_project
from services.project_workspace_service import sync_project_workspace
from services.storage_service import storage_service
from services.truth_verification_service import create_truth_verification_run

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_payload(project: Project, workspace_summary=None):
    return ProjectResponse(
        id=project.id,
        hospitalId=project.hospital_id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        status=project.status,
        payerScope=project.payer_scope,
        workspaceDuckdbPath=project.workspace_duckdb_path,
        storagePrefix=project.storage_prefix,
        workspaceSummary=workspace_summary,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(Project).where(Project.hospital_id == current_user["hospital_id"]).order_by(Project.created_at.desc())
        )
        return [_project_payload(project) for project in rows.scalars().all()]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreateRequest, current_user: dict = Depends(get_current_user)):
    project = await create_project_for_hospital(
        hospital_id=current_user["hospital_id"],
        created_by=current_user["id"],
        name=request.name,
        description=request.description,
        payer_scope=request.payerScope,
    )
    workspace = await sync_project_workspace(project)
    return _project_payload(project, workspace)


@router.post("/ensure-default", response_model=ProjectResponse)
async def ensure_project(current_user: dict = Depends(get_current_user)):
    project = await ensure_default_project(current_user["hospital_id"], current_user["id"])
    workspace = await sync_project_workspace(project)
    return _project_payload(project, workspace)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        project = (
            await db.execute(
                select(Project).where(Project.id == project_id, Project.hospital_id == current_user["hospital_id"])
            )
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        workspace = await sync_project_workspace(project)
        return _project_payload(project, workspace)


@router.post("/{project_id}/storage/presign", response_model=StoragePresignResponse)
async def presign_storage(project_id: str, request: StoragePresignRequest, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        project = (
            await db.execute(
                select(Project).where(Project.id == project_id, Project.hospital_id == current_user["hospital_id"])
            )
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    storage_key = request.storageKey or storage_service.build_key(
        prefix=request.prefix or f"projects/{project_id}/staging",
        filename=request.fileName or "upload.bin",
        namespace=current_user["hospital_id"],
    )
    signed = storage_service.presign(storage_key=storage_key, operation=request.operation)
    return StoragePresignResponse(**signed)


@router.post("/{project_id}/verify", response_model=TruthVerificationResponse)
async def verify_project_truth(project_id: str, request: TruthVerificationRequest, current_user: dict = Depends(get_current_user)):
    run = await create_truth_verification_run(
        project_id=project_id,
        hospital_id=current_user["hospital_id"],
        created_by=current_user["id"],
        batch_run_id=request.batchRunId,
    )
    return TruthVerificationResponse(
        id=run.id,
        projectId=run.project_id,
        batchRunId=run.batch_run_id,
        status=run.status,
        verificationSummary=run.verification_summary or {},
        createdAt=run.created_at,
        completedAt=run.completed_at,
    )


@router.get("/{project_id}/verification-runs", response_model=list[TruthVerificationResponse])
async def list_verification_runs(project_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(TruthVerificationRun).where(
                TruthVerificationRun.project_id == project_id,
                TruthVerificationRun.hospital_id == current_user["hospital_id"],
            ).order_by(TruthVerificationRun.created_at.desc())
        )
        return [
            TruthVerificationResponse(
                id=row.id,
                projectId=row.project_id,
                batchRunId=row.batch_run_id,
                status=row.status,
                verificationSummary=row.verification_summary or {},
                createdAt=row.created_at,
                completedAt=row.completed_at,
            )
            for row in rows.scalars().all()
        ]


@router.post("/{project_id}/audit-runs", response_model=FormalAuditRunResponse)
async def create_audit_run(project_id: str, request: FormalAuditRunCreateRequest, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        project = (
            await db.execute(
                select(Project).where(Project.id == project_id, Project.hospital_id == current_user["hospital_id"])
            )
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    run = await create_formal_audit_run(
        project=project,
        hospital_id=current_user["hospital_id"],
        created_by=current_user["id"],
        batch_run_id=request.batchRunId,
        verification_run_id=request.verificationRunId,
    )
    return FormalAuditRunResponse(
        id=run.id,
        projectId=run.project_id,
        batchRunId=run.batch_run_id,
        verificationRunId=run.verification_run_id,
        status=run.status,
        auditStandard=run.audit_standard,
        report=run.report_json or {},
        createdAt=run.created_at,
        completedAt=run.completed_at,
    )


@router.get("/{project_id}/audit-runs", response_model=list[FormalAuditRunResponse])
async def list_audit_runs(project_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(FormalAuditRun).where(
                FormalAuditRun.project_id == project_id,
                FormalAuditRun.hospital_id == current_user["hospital_id"],
            ).order_by(FormalAuditRun.created_at.desc())
        )
        return [
            FormalAuditRunResponse(
                id=row.id,
                projectId=row.project_id,
                batchRunId=row.batch_run_id,
                verificationRunId=row.verification_run_id,
                status=row.status,
                auditStandard=row.audit_standard,
                report=row.report_json or {},
                createdAt=row.created_at,
                completedAt=row.completed_at,
            )
            for row in rows.scalars().all()
        ]
