from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import DocumentChunk
from app.services.llm_client import embed_query


@dataclass
class RetrievedChunk:
    source: str
    category: str
    content: str
    distance: float


def retrieve(db: Session, query: str, top_k: int | None = None, category: str | None = None) -> list[RetrievedChunk]:
    """Embed the query and return the top_k nearest document chunks via pgvector cosine distance."""
    top_k = top_k or settings.RAG_TOP_K
    query_embedding = embed_query(query)

    stmt = select(
        DocumentChunk.source,
        DocumentChunk.category,
        DocumentChunk.content,
        DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
    ).order_by("distance").limit(top_k)

    if category:
        stmt = stmt.where(DocumentChunk.category == category)

    rows = db.execute(stmt).all()
    return [RetrievedChunk(source=r.source, category=r.category, content=r.content, distance=r.distance) for r in rows]


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant knowledge-base context found."
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c.source} | {c.category}]\n{c.content}")
    return "\n\n".join(parts)
