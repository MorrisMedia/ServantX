# ServantX productionization notes

## What is now scaffolded

### Backend runtime
- Centralized settings layer in `servantx-backend/config.py`
- Production/non-dev database resolution defaults to Postgres
- Local dev still defaults to SQLite when `DATABASE_URL` is not set
- Health endpoint now reports database + storage readiness
- API/worker/migrate roles are supported through `servantx-backend/start.sh`

### Data stores
- **Postgres-ready** via `DATABASE_URL` / `POSTGRES_*`
- **Redis-ready** via `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- **S3-compatible object storage ready** via `STORAGE_BACKEND=s3`
  - works with AWS S3, Cloudflare R2, MinIO, DigitalOcean Spaces, etc.
  - local storage remains available with `STORAGE_BACKEND=local`
- DuckDB project workspaces now resolve from `DUCKDB_WORKSPACE_ROOT`

### Deployment scaffolding
- `servantx-backend/compose.yaml` now stands up:
  - postgres
  - redis
  - minio
  - backend API
  - celery worker
  - bucket bootstrap helper
- `servantx-backend/compose.dev.yaml` keeps a dev-oriented local stack
- `servantx-backend/.env.production.example` and `servantx-frontend/.env.production.example` document hosted env shape

### Hosted smoke flow
- Backend: `servantx-backend/scripts/smoke_hosted.sh`
- Frontend: `cd servantx-frontend && SMOKE_BASE_URL=https://app.example.com npm run smoke`

## Required secrets / credentials for a real deployment

### Required
- `JWT_SECRET_KEY`
- Postgres credentials / `DATABASE_URL`
- Redis URL (if async Celery is enabled, which production should use)
- S3-compatible storage credentials:
  - `STORAGE_BUCKET`
  - `STORAGE_ACCESS_KEY_ID`
  - `STORAGE_SECRET_ACCESS_KEY`
  - optional `STORAGE_ENDPOINT_URL` for non-AWS vendors

### Optional but expected for full product behavior
- `OPENAI_API_KEY`
- `SENDGRID_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Example deployment paths

### Local production-like stack
```bash
cd servantx-backend
cp .env.production.example .env
# fill in real secrets
docker compose -f compose.yaml up --build -d
```

### Backend smoke
```bash
cd servantx-backend
API_BASE_URL=https://api.example.com ./scripts/smoke_hosted.sh
```

### Frontend smoke
```bash
cd servantx-frontend
npm install
npx playwright install chromium
SMOKE_BASE_URL=https://app.example.com \
SMOKE_EMAIL=qa@example.com \
SMOKE_PASSWORD='super-secret' \
npm run smoke
```

## Notes
- `/files/*` is intentionally only served directly when `STORAGE_BACKEND=local`.
- For S3-backed deployments, project presign responses now point at the object store instead.
- Deterministic repricing logic was left intact.
