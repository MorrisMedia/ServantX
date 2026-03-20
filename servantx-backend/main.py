from pathlib import Path

import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from routes.admin_rates import router as admin_rates_router
from routes.analysis import router as analysis_router
from routes.appeals import router as appeals_router
from routes.auth import router as auth_router
from routes.batches import router as batches_router
from routes.contact import router as contact_router
from routes.contracts import router as contracts_router
from routes.documents import router as documents_router
from routes.projects import router as projects_router
from routes.receipts import router as receipts_router
from routes.rules import router as rules_router
from sqlalchemy import text

from config import settings
from core_services.db_service import IS_SQLITE, AsyncSessionLocal, bootstrap_schema_if_needed, engine
from services.rate_seed_service import auto_seed_rate_data
from services.storage_service import storage_service


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for ServantX",
    version=settings.APP_VERSION,
)


@app.on_event("startup")
async def startup_bootstrap_local_db():
    try:
        if settings.AUTO_BOOTSTRAP_SQLITE and (IS_SQLITE or settings.is_vercel):
            await bootstrap_schema_if_needed(force=settings.is_vercel and not IS_SQLITE)

        if settings.AUTO_SEED_RATE_DATA:
            async with AsyncSessionLocal() as db:
                await auto_seed_rate_data(db)
    except Exception as exc:
        print(f"Startup bootstrap warning: {exc}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(contracts_router)
app.include_router(receipts_router)
app.include_router(rules_router)
app.include_router(batches_router)
app.include_router(analysis_router)
app.include_router(appeals_router)
app.include_router(admin_rates_router)
app.include_router(documents_router)
app.include_router(projects_router)


@app.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    if settings.STORAGE_BACKEND != "local":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Direct file serving is disabled for non-local storage backends.",
        )

    full_path = storage_service.resolve_local_path(file_path)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(full_path)


@app.get("/")
async def root():
    return {
        "message": settings.APP_NAME,
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "deploymentTarget": settings.DEPLOYMENT_TARGET,
        "storageBackend": settings.STORAGE_BACKEND,
    }


@app.get("/health")
async def health():
    db_ok = True
    db_error = None
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    storage_status = storage_service.healthcheck()
    overall_ok = db_ok and storage_status.get("ok", False)
    return {
        "status": "healthy" if overall_ok else "degraded",
        "service": "servantx-api",
        "environment": settings.ENVIRONMENT,
        "database": {"ok": db_ok, "engine": "sqlite" if settings.is_sqlite else "postgres", "error": db_error},
        "storage": storage_status,
        "celery": {
            "enabled": settings.celery_async_enabled,
            "broker": settings.resolved_celery_broker_url,
            "resultBackend": settings.resolved_celery_result_backend,
        },
    }
