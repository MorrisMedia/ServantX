# ServantX Backend

FastAPI backend for medical-claim audit workflows.

## What changed

This foundation now includes:
- project-centered audit workspaces
- presign-ready local storage abstraction
- DuckDB project workspace materialization
- truth verification runs
- formal audit runs layered on existing deterministic repricing

## Local development

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Docker Compose

```bash
docker compose -f compose.dev.yaml up --build
```

This starts Postgres, Redis, the API, and the Celery worker with uploads persisted to a named volume.

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
- `POST /batches/upload-835` now auto-attaches to a project workspace

## Storage + DuckDB

Uploads remain local by default, but the API now returns presign metadata shaped for a future object-store swap. Each project gets a DuckDB file under `uploads/workspaces/<project-slug>/project.duckdb` containing materialized audit tables:

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

## Health

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`
