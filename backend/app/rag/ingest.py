"""
Ingests the sample knowledge-base documents under backend/sample_docs/ into
the document_chunks table with local embeddings, for the RAG agent to query.

Usage:
    python -m app.rag.ingest

Documents are plain-text/markdown files. Each file's front-matter-like first
line `category: <name>` sets the category; the rest is chunked by paragraph.
Swap in real documents later by dropping more files into sample_docs/ (or
pointing SAMPLE_DOCS_DIR elsewhere) and re-running this script.

Note: embeddings run locally (see app.services.llm_client), so this doesn't
need GROQ_API_KEY at all - only the chat/recommendation agents do. The first
run downloads the embedding model (~500MB) from HuggingFace/GCS if it isn't
already baked into the Docker image (see backend/Dockerfile).
"""
from pathlib import Path

from app.core.logging import configure_logging, get_logger
from app.db.models import DocumentChunk
from app.db.session import SessionLocal
from app.services.llm_client import embed_document

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_docs"
CHUNK_MIN_CHARS = 200

logger = get_logger("rag.ingest")


def _chunk_document(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        buffer = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(buffer) >= CHUNK_MIN_CHARS:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


def ingest_all() -> None:
    configure_logging()
    if not SAMPLE_DOCS_DIR.exists():
        logger.warning("sample_docs_dir_missing", path=str(SAMPLE_DOCS_DIR))
        return

    db = SessionLocal()
    try:
        # Idempotent for demo purposes: clear existing chunks before re-ingesting.
        db.query(DocumentChunk).delete()

        total_chunks = 0
        for file_path in sorted(SAMPLE_DOCS_DIR.glob("*.md")):
            raw = file_path.read_text(encoding="utf-8")
            lines = raw.splitlines()
            category = "general"
            if lines and lines[0].startswith("category:"):
                category = lines[0].split(":", 1)[1].strip()
                raw = "\n".join(lines[1:])

            for chunk in _chunk_document(raw):
                embedding = embed_document(chunk)
                db.add(
                    DocumentChunk(
                        source=file_path.name,
                        category=category,
                        content=chunk,
                        embedding=embedding,
                    )
                )
                total_chunks += 1

        db.commit()
        logger.info("rag_ingest_complete", files=len(list(SAMPLE_DOCS_DIR.glob('*.md'))), chunks=total_chunks)
    finally:
        db.close()


if __name__ == "__main__":
    ingest_all()
