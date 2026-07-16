"""
LLM services for the app, split across two providers deliberately:

  - Chat text generation: Groq's free-tier API (OpenAI-compatible chat
    completions, served on Groq's LPU hardware). Needs GROQ_API_KEY.

  - Embeddings: run locally via fastembed (ONNX runtime, no PyTorch, no
    GPU needed), not via an external API. This is intentional after
    repeatedly hitting embedding-API instability in practice (a provider
    deprecating its embedding model, a billing change, an embeddings
    endpoint advertised in an SDK but not actually live) - local embeddings
    have no API key, no quota, no billing, and no "endpoint doesn't exist"
    failure mode. The model (BAAI/bge-base-en-v1.5) has a fixed, unambiguous
    768-dim output - deliberately avoiding Matryoshka-resizable models like
    nomic-embed-text, where the *advertised* dimension and what a given
    library version actually emits can disagree. _embed() double-checks the
    real output width against settings.EMBEDDING_DIM at runtime and fails
    loudly and immediately if they ever drift apart again, rather than
    letting a mismatch surface three layers down as a Postgres error.

Get a free Groq API key (no credit card) at https://console.groq.com/keys.
"""
from __future__ import annotations

from groq import Groq, RateLimitError
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("llm_client")

_groq_client: Groq | None = None
_embedding_model = None  # lazy-loaded fastembed.TextEmbedding singleton


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM provider can't serve a request (e.g. rate-limited).

    Agents catch this to degrade gracefully instead of letting a raw
    provider error surface as a 500 to the user.
    """


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            logger.warning("groq_api_key_missing", hint="Set GROQ_API_KEY to call Groq")
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding

        logger.info("loading_embedding_model", model=settings.FASTEMBED_MODEL_NAME)
        kwargs = {"model_name": settings.FASTEMBED_MODEL_NAME}
        if settings.FASTEMBED_CACHE_PATH:
            kwargs["cache_dir"] = settings.FASTEMBED_CACHE_PATH
        _embedding_model = TextEmbedding(**kwargs)
    return _embedding_model


# Rate-limit errors are not transient in the way network blips are - retrying
# with the same key just reproduces the same 429, so we skip the retry loop
# for them and fail fast instead of wasting several seconds per call.
_RETRY_UNLESS_RATE_LIMITED = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_not_exception_type(RateLimitError),
    reraise=True,
)


@_RETRY_UNLESS_RATE_LIMITED
def generate_text(prompt: str, system_instruction: str | None = None, temperature: float = 0.4) -> str:
    """Single-shot chat completion against Groq's free-tier Llama model."""
    client = _get_groq_client()
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_CHAT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        logger.info("llm_call", model=settings.GROQ_CHAT_MODEL, prompt_chars=len(prompt))
        return response.choices[0].message.content
    except RateLimitError as exc:
        logger.error("llm_rate_limited", model=settings.GROQ_CHAT_MODEL)
        raise LLMUnavailableError(
            "Groq's free-tier rate limit was hit for this key. Wait a bit and retry, or "
            "check console.groq.com for your current limits."
        ) from exc


class EmbeddingDimensionMismatchError(RuntimeError):
    """Raised when the embedding model's real output width doesn't match EMBEDDING_DIM.

    Fails immediately and clearly at the point of embedding, instead of
    letting a mismatched vector reach Postgres and surface as an opaque
    'expected N dimensions, not M' error several layers down.
    """


# BGE models use an asymmetric convention: queries get a search instruction
# prefix, documents/passages get no prefix at all.
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def embed_document(text: str) -> list[float]:
    """Embed a knowledge-base chunk for storage (no prefix, per BGE convention)."""
    return _embed(text)


def embed_query(text: str) -> list[float]:
    """Embed a user question for similarity search (BGE query instruction prefix)."""
    return _embed(f"{_BGE_QUERY_PREFIX}{text}")


def embed_text(text: str) -> list[float]:
    """Back-compat generic embedding entrypoint. Prefer embed_document()/embed_query()."""
    return _embed(text)


def _embed(text: str) -> list[float]:
    model = _get_embedding_model()
    embedding = next(model.embed([text])).tolist()
    if len(embedding) != settings.EMBEDDING_DIM:
        raise EmbeddingDimensionMismatchError(
            f"Embedding model '{settings.FASTEMBED_MODEL_NAME}' produced a "
            f"{len(embedding)}-dim vector, but EMBEDDING_DIM is configured as "
            f"{settings.EMBEDDING_DIM}. Update EMBEDDING_DIM (and the pgvector "
            f"column width via an Alembic migration) to match, or switch to a "
            f"model that natively outputs {settings.EMBEDDING_DIM} dimensions."
        )
    return embedding
