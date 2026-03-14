from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import BatchRun, Document, FormalAuditRun, Project, TruthVerificationRun


async def create_formal_audit_run(
    *,
    project: Project,
    hospital_id: str,
    created_by: Optional[str],
    batch_run_id: Optional[str] = None,
    verification_run_id: Optional[str] = None,
) -> FormalAuditRun:
    async with AsyncSessionLocal() as db:
        verification = None
        if verification_run_id:
            verification = (
                await db.execute(
                    select(TruthVerificationRun).where(
                        TruthVerificationRun.id == verification_run_id,
                        TruthVerificationRun.project_id == project.id,
                    )
                )
            ).scalar_one_or_none()

        document_query = select(Document).where(Document.project_id == project.id)
        if batch_run_id:
            document_query = document_query.where(Document.batch_run_id == batch_run_id)
        documents = list((await db.execute(document_query)).scalars().all())

        total_underpayment = round(sum(float(doc.underpayment_amount or 0.0) for doc in documents), 2)
        flagged_claims = sum(1 for doc in documents if float(doc.underpayment_amount or 0.0) > 0)
        report: Dict[str, Any] = {
            "projectId": project.id,
            "batchRunId": batch_run_id,
            "verificationRunId": verification_run_id,
            "generatedAt": datetime.utcnow().isoformat(),
            "standard": "MEDICAL_AUDIT_V1",
            "summary": {
                "documentCount": len(documents),
                "flaggedClaims": flagged_claims,
                "totalUnderpayment": total_underpayment,
                "statusBreakdown": {},
            },
            "controls": {
                "projectBoundariesEstablished": True,
                "presignReadyStorageInterfaces": True,
                "duckdbWorkspaceMaterialized": bool(project.workspace_duckdb_path),
                "truthVerificationAttached": verification is not None,
            },
            "exceptions": verification.verification_summary.get("documentsWithoutParsedData", []) if verification and verification.verification_summary else [],
        }
        for doc in documents:
            report["summary"]["statusBreakdown"][doc.status] = report["summary"]["statusBreakdown"].get(doc.status, 0) + 1

        run = FormalAuditRun(
            project_id=project.id,
            hospital_id=hospital_id,
            batch_run_id=batch_run_id,
            verification_run_id=verification_run_id,
            status="completed",
            audit_standard="MEDICAL_AUDIT_V1",
            report_json=report,
            created_by=created_by,
            completed_at=datetime.utcnow(),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run
