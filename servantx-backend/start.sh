#!/bin/bash

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-servantx}

if [ -z "${DATABASE_URL}" ]; then
    export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DB_HOST}:${DB_PORT}/${POSTGRES_DB}"
fi

echo "Waiting for database to be ready..."
while ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${POSTGRES_USER}; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

echo "Creating database if it doesn't exist..."
python3 /app/core_services/create_db.py

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
if [ "${ENVIRONMENT}" = "development" ]; then
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    exec uvicorn main:app --host 0.0.0.0 --port 8000
fi
