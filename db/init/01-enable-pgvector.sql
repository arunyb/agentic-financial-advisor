-- Runs automatically the first time the postgres_data volume is created
-- (Postgres's official image executes every .sql file here on an empty
-- data directory only). This guarantees pgvector is enabled before Alembic
-- migrations run, even though the migration also does this defensively.
CREATE EXTENSION IF NOT EXISTS vector;
