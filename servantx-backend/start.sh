#!/bin/bash
set -euo pipefail

ROLE=${SERVICE_ROLE:-api}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-servantx}
APP_HOST=${APP_HOST:-0.0.0.0}
APP_PORT=${APP_PORT:-8000}

if [ -z "${DATABASE_URL:-}" ] && [ "${ENVIRONMENT:-development}" != "development" ]; then
  export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DB_HOST}:${DB_PORT}/${POSTGRES_DB}"
fi

if [[ "${DATABASE_URL:-}" == postgresql* ]] || [[ -n "${DB_HOST:-}" && "${ENVIRONMENT:-development}" != "development" ]]; then
  echo "Waiting for database ${DB_HOST}:${DB_PORT}..."
  until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
    echo "Database unavailable - sleeping"
    sleep 2
  done
  echo "Database is ready"
  python3 /app/core_services/create_db.py || true
  alembic upgrade head
fi

case "$ROLE" in
  api)
    if [ "${ENVIRONMENT:-development}" = "development" ]; then
      exec uvicorn main:app --host "$APP_HOST" --port "$APP_PORT" --reload
    else
      exec uvicorn main:app --host "$APP_HOST" --port "$APP_PORT"
    fi
    ;;
  worker)
    exec celery -A celery_app.celery_app worker --loglevel="${CELERY_LOG_LEVEL:-info}" -Q ingest,parse,review,synthesize,reconcile
    ;;
  beat)
    exec celery -A celery_app.celery_app beat --loglevel="${CELERY_LOG_LEVEL:-info}"
    ;;
  migrate)
    echo "Migrations complete"
    ;;
  *)
    echo "Unknown SERVICE_ROLE: $ROLE" >&2
    exit 1
    ;;
esac
