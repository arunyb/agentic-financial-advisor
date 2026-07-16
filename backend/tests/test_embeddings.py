import numpy as np
import pytest

from app.core.config import settings
from app.services import llm_client


@pytest.fixture(autouse=True)
def mock_llm():
    """
    Shadows conftest's autouse `mock_llm` fixture for this file only: these
    tests exercise the real embed_document()/embed_query()/_embed() prefix
    and dimension-check logic directly, so nothing should be pre-mocked here.
    """
    yield


def test_embed_raises_clear_error_on_dimension_mismatch(monkeypatch):
    """
    If the embedding model's real output width ever disagrees with
    EMBEDDING_DIM again (as happened once during development), this must
    fail immediately with a clear, actionable message - not silently reach
    Postgres and surface as an opaque 'expected N dimensions, not M' error.
    """

    class FakeModel:
        def embed(self, texts):
            for _ in texts:
                yield np.array([0.1] * (settings.EMBEDDING_DIM - 1))  # deliberately wrong

    monkeypatch.setattr(llm_client, "_get_embedding_model", lambda: FakeModel())

    with pytest.raises(llm_client.EmbeddingDimensionMismatchError, match="produced a"):
        llm_client.embed_document("some text")


def test_embed_succeeds_when_dimension_matches(monkeypatch):
    class FakeModel:
        def embed(self, texts):
            for _ in texts:
                yield np.array([0.1] * settings.EMBEDDING_DIM)

    monkeypatch.setattr(llm_client, "_get_embedding_model", lambda: FakeModel())

    result = llm_client.embed_document("some text")
    assert len(result) == settings.EMBEDDING_DIM


def test_embed_query_and_document_use_different_prefixes(monkeypatch):
    """BGE models want an instruction prefix on queries but not on documents."""
    captured = {}

    class FakeModel:
        def embed(self, texts):
            captured["text"] = texts[0]
            for _ in texts:
                yield np.array([0.1] * settings.EMBEDDING_DIM)

    monkeypatch.setattr(llm_client, "_get_embedding_model", lambda: FakeModel())

    llm_client.embed_document("hello world")
    assert captured["text"] == "hello world"

    llm_client.embed_query("hello world")
    assert captured["text"].endswith("hello world")
    assert captured["text"] != "hello world"  # query got a prefix, document didn't
