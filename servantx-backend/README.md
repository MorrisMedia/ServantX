# ServantX Backend

FastAPI backend for medical-claim audit workflows.

## What changed

This rebuild now includes:
- project-centered audit workspaces
- centralized env/config scaffolding for dev + production
- Postgres-ready SQLAlchemy runtime with SQLite preserved for local dev
- Redis/Celery-ready worker configuration
- S3-compatible object storage support with local-storage fallback
- Vercel deployment mode with Vercel Blob storage support and inline task execution
- DuckDB project workspace materialization
- truth verification runs
- formal audit runs layered on existing deterministic repricing

## Local development

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.local.example .env
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Docker Compose

```bash
docker compose -f compose.dev.yaml up --build
```

This starts Postgres, Redis, the API, and the Celery worker with uploads persisted to a named volume.

## Production scaffold

Copy `.env.production.example` to `.env`, fill in real values, then run:

```bash
docker compose -f compose.yaml up --build -d
```

The production compose scaffold includes Postgres, Redis, MinIO, the API, and a dedicated Celery worker.

## Vercel mode

Vercel mode keeps the existing full production architecture intact, but adds a pragmatic single-function deployment mode for `servantx-backend`.

### What Vercel mode changes

- disables Celery/Redis-driven async processing in favor of inline execution
- supports `STORAGE_BACKEND=vercel_blob` for uploaded files and generated appeal artifacts
- reads Vercel Postgres env vars (`DATABASE_URL`, `POSTGRES_URL`, `POSTGRES_URL_NON_POOLING`)
- uses `/tmp/uploads` and `/tmp/uploads/workspaces` for ephemeral local workspace paths when needed
- routes all requests to `main.py` via `vercel.json`

### Recommended env vars

Start from `.env.vercel.example`.

Required for a practical Vercel deployment:
- `ENVIRONMENT=production`
- `DEPLOYMENT_TARGET=vercel`
- `JWT_SECRET_KEY=...`
- `STORAGE_PRESIGN_SECRET=...`
- `STORAGE_BACKEND=vercel_blob`
- `BLOB_READ_WRITE_TOKEN=...`
- `FORCE_INLINE_TASKS=true`
- `ENABLE_CELERY_ASYNC=false`
- `POSTGRES_URL` or `DATABASE_URL` from the linked Vercel Postgres integration
- `API_BASE_URL=https://<your-backend>.vercel.app`
- `FRONTEND_URL=https://<your-frontend>.vercel.app`
- `CORS_ORIGINS=https://<your-frontend>.vercel.app`

### Notes / caveats

- Server uploads on Vercel functions are best kept under Vercel's request-size limits.
- Large direct server uploads are a poor fit for Vercel Functions; if needed later, add a client-upload flow for Blob.
- Inline processing is intentional in Vercel mode; it trades throughput for deploy simplicity.
- The existing Docker/Celery/S3 architecture is still the better fit for sustained heavy batch processing.

## New core endpoints

- `GET /projects`
- `POST /projects`
- `POST /projects/ensure-default`
- `GET /projects/{projectId}`
- `POST /projects/{projectId}/storage/presign`
- `POST /projects/{projectId}/verify`
- `GET /projects/{projectId}/verification-runs`
- `POST /projects/{projectId}/audit-runs`
- `GET /projects/{projectId}/audit-runs`
- `POST /batches/upload-835` auto-attaches to a project workspace

## Storage + DuckDB

### Local
- `STORAGE_BACKEND=local`
- files are served from `/files/*`

### Production object storage
- `STORAGE_BACKEND=s3`
- supports AWS S3 and S3-compatible vendors (R2, MinIO, DO Spaces, etc.)
- project presign metadata returns actual object-store presigned URLs

### Vercel Blob
- `STORAGE_BACKEND=vercel_blob`
- requires `BLOB_READ_WRITE_TOKEN`
- uploaded files and generated appeal assets are persisted in Vercel Blob instead of the local filesystem
- document extraction paths now read through the storage abstraction instead of assuming `uploads/` exists on disk

Each project gets a DuckDB file under `DUCKDB_WORKSPACE_ROOT` (default `uploads/workspaces`, resolved to `/tmp/uploads/workspaces` on Vercel) containing materialized audit tables:
- `servantx.batch_runs`
- `servantx.documents`
- `servantx.parsed_claims`
- `servantx.audit_findings`

## Migration

Run:

```bash
alembic upgrade head
```

The project spine migration adds projects, project artifacts, truth verification runs, formal audit runs, and project foreign keys on contracts/receipts/batches/documents.

## Hosted smoke

### Backend
```bash
API_BASE_URL=https://api.example.com ./scripts/smoke_hosted.sh
```

### Frontend
See `../PRODUCTION.md` and `servantx-frontend/smoke-test.mjs`.

## Health

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`
