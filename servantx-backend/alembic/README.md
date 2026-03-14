# Generate a new migration (auto-detect changes from models)

docker exec -it servantx-backend alembic revision --autogenerate -m "Initial migration"

# Run all pending migrations

alembic upgrade head

# Rollback one migration

alembic downgrade -1

# View current migration status

alembic current

# View migration history

alembic history
