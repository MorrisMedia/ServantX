from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / '.env')

from core_services.db_service import AsyncSessionLocal
from models import BatchRun, Document, DocumentRole, Project, User
from services.audit_pipeline_service import run_stage1_ingest_835_file, run_stage4_summarize_batch
from services.project_service import ensure_default_project
from services.storage_service import storage_service


async def run_demo(count: int, payer_scope: str, sample_path: Path) -> dict:
    sample_bytes = sample_path.read_bytes()

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).order_by(User.created_at.asc()))).scalars().first()
        if not user:
            raise RuntimeError('No local user found')

        project = await ensure_default_project(user.hospital_id, user.id)

        batch = BatchRun(
            hospital_id=user.hospital_id,
            project_id=project.id,
            status='queued',
            payer_scope=payer_scope,
            source_file_count=count,
            claim_document_count=0,
            processed_claim_count=0,
            failed_claim_count=0,
            started_at=datetime.utcnow(),
        )
        db.add(batch)
        await db.flush()

        file_doc_ids = []
        for idx in range(count):
            saved = storage_service.save_bytes(
                content=sample_bytes,
                filename=f'medicare-demo-{idx+1}.835',
                prefix=f'projects/{project.id}/eras',
                namespace=user.hospital_id,
                content_type='text/plain',
            )
            doc = Document(
                receipt_id=None,
                hospital_id=user.hospital_id,
                project_id=project.id,
                batch_run_id=batch.id,
                contract_id=None,
                document_role=DocumentRole.FILE,
                parent_document_id=None,
                payer_key=None,
                source_file_name=f'medicare-demo-{idx+1}.835',
                source_file_path=saved['storage_key'],
                name=f'Medicare Demo {idx+1}',
                status='queued_ingest',
                amount=0.0,
                receipt_amount=0.0,
                contract_amount=0.0,
                underpayment_amount=0.0,
                notes=f"sha256={saved['sha256']}",
                rules_applied=None,
            )
            db.add(doc)
            await db.flush()
            file_doc_ids.append(doc.id)

        await db.commit()
        batch_id = batch.id

    for file_doc_id in file_doc_ids:
        await run_stage1_ingest_835_file(file_doc_id, batch_id)

    summary = await run_stage4_summarize_batch(batch_id)

    async with AsyncSessionLocal() as db:
        batch = (await db.execute(select(BatchRun).where(BatchRun.id == batch_id))).scalar_one()
        claim_docs = (await db.execute(select(Document).where(Document.batch_run_id == batch_id, Document.document_role == DocumentRole.CLAIM))).scalars().all()
        return {
            'batch_id': batch_id,
            'payer_scope': batch.payer_scope,
            'status': batch.status,
            'source_file_count': batch.source_file_count,
            'claim_document_count': len(claim_docs),
            'executive_summary': batch.executive_summary,
            'reconciliation_json': batch.reconciliation_json,
            'summary_result': summary,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a local 835 demo batch through the ServantX pipeline')
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--payer-scope', default='MEDICARE')
    parser.add_argument('--sample', default=str(ROOT / 'smoke_sample.835'))
    args = parser.parse_args()
    result = asyncio.run(run_demo(count=args.count, payer_scope=args.payer_scope, sample_path=Path(args.sample)))
    print(json.dumps(result, indent=2, default=str))
