"""
Regression test for a real bug hit during development: the Alembic
migration's hardcoded VECTOR(dim=N) silently drifted from
settings.EMBEDDING_DIM, causing every RAG ingestion to fail with a
Postgres-level "expected N dimensions, not M" error. Since Alembic
migrations are static generated files (not re-evaluated from the model at
runtime), this can't be caught by just reading app/db/models.py - it has to
be checked against the database schema Alembic actually produces.
"""
from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.session import engine


def test_document_chunks_embedding_column_matches_configured_dimension():
    with engine.connect() as conn:
        inspector = inspect(conn)
        assert "document_chunks" in inspector.get_table_names(), (
            "document_chunks table not found - did migrations run?"
        )

        result = conn.execute(
            text(
                "SELECT atttypmod FROM pg_attribute "
                "WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding'"
            )
        ).scalar()

        # pgvector stores the declared dimension directly in atttypmod for VECTOR columns.
        assert result == settings.EMBEDDING_DIM, (
            f"document_chunks.embedding is declared as vector({result}) in the database, "
            f"but settings.EMBEDDING_DIM is {settings.EMBEDDING_DIM}. These must match - "
            f"check the Alembic migration's hardcoded VECTOR(dim=...) value."
        )
