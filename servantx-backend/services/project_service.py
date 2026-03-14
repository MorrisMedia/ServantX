import re
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import BatchRun, Project


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


async def get_project(project_id: str, hospital_id: str) -> Optional[Project]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.id == project_id, Project.hospital_id == hospital_id)
        )
        return result.scalar_one_or_none()


async def list_projects(hospital_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.hospital_id == hospital_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())


async def create_project_for_hospital(
    *,
    hospital_id: str,
    created_by: Optional[str],
    name: str,
    description: Optional[str] = None,
    payer_scope: Optional[str] = None,
) -> Project:
    async with AsyncSessionLocal() as db:
        base_slug = slugify(name)
        slug = base_slug
        attempt = 2
        while True:
            existing = await db.execute(
                select(Project).where(Project.hospital_id == hospital_id, Project.slug == slug)
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{attempt}"
            attempt += 1

        project = Project(
            hospital_id=hospital_id,
            name=name,
            slug=slug,
            description=description,
            payer_scope=payer_scope or "MEDICARE_TX_MEDICAID_FFS",
            storage_prefix=f"projects/{slug}",
            workspace_duckdb_path=f"workspaces/{slug}/project.duckdb",
            created_by=created_by,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project


async def ensure_default_project(hospital_id: str, created_by: Optional[str] = None) -> Project:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.hospital_id == hospital_id).order_by(Project.created_at.asc())
        )
        project = result.scalars().first()
        if project:
            return project

    return await create_project_for_hospital(
        hospital_id=hospital_id,
        created_by=created_by,
        name="Primary Audit Workspace",
        description="Default project workspace for batch ingest and audit runs.",
    )


async def resolve_project_for_batch(batch: BatchRun) -> Optional[Project]:
    if not batch.project_id:
        return None
    return await get_project(batch.project_id, batch.hospital_id)


def ensure_workspace_directory(relative_duckdb_path: str) -> Path:
    path = Path("uploads") / relative_duckdb_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
