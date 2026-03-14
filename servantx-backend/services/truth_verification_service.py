from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, Optional

from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import AuditFinding, BatchRun, Document, ParsedData, TruthVerificationRun
from services.project_workspace_service import sync_project_workspace
from services.project_service import get_project


async def create_truth_verification_run(
    *,
    project_id: str,
    hospital_id: str,
    created_by: Optional[str],
    batch_run_id: Optional[str] = None,
) -> TruthVerificationRun:
    async with AsyncSessionLocal() as db:
        run = TruthVerificationRun(
            project_id=project_id,
            hospital_id=hospital_id,
            batch_run_id=batch_run_id,
            status="running",
            created_by=created_by,
        )
        db.add(run)
        await db.flush()

        document_query = select(Document).where(Document.project_id == project_id)
        if batch_run_id:
            document_query = document_query.where(Document.batch_run_id == batch_run_id)
        documents = list((await db.execute(document_query)).scalars().all())
        doc_ids = [doc.id for doc in documents]

        parsed_rows = []
        findings = []
        if doc_ids:
            parsed_rows = list((await db.execute(select(ParsedData).where(ParsedData.document_id.in_(doc_ids)))).scalars().all())
            findings = list((await db.execute(select(AuditFinding).where(AuditFinding.document_id.in_(doc_ids)))).scalars().all())

        artifact_hashes = []
        for parsed in parsed_rows:
            artifact_hashes.append(sha256(str(parsed.payload or {}).encode()).hexdigest())

        summary: Dict[str, Any] = {
            "projectId": project_id,
            "batchRunId": batch_run_id,
            "documentCount": len(documents),
            "parsedRecordCount": len(parsed_rows),
            "findingCount": len(findings),
            "documentsWithoutParsedData": sorted(set(doc_ids) - {row.document_id for row in parsed_rows}),
            "findingDistribution": {},
            "evidenceDigest": sha256("|".join(sorted(artifact_hashes)).encode()).hexdigest() if artifact_hashes else None,
            "verifiedAt": datetime.utcnow().isoformat(),
        }
        for finding in findings:
            summary["findingDistribution"][finding.finding_code] = summary["findingDistribution"].get(finding.finding_code, 0) + 1

        project = await get_project(project_id, hospital_id)
        if project:
            summary["workspace"] = await sync_project_workspace(project)

        run.status = "verified"
        run.verification_summary = summary
        run.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(run)
        return run
