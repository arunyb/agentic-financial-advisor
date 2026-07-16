FROM python:3.12-slim AS base

# System deps needed to build psycopg2 from source wheels on some platforms
# and give a working locale/timezone data set for a financial app.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Pre-bake the local embedding model into the image at build time. This means
# containers never need network access to HuggingFace/GCS at runtime, startup
# is fast, and RAG ingestion works even in network-restricted deployments.
ENV FASTEMBED_CACHE_PATH=/app/.fastembed_cache
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-base-en-v1.5', cache_dir='/app/.fastembed_cache')"

COPY . .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# In production, run behind a reverse proxy / process manager and consider
# multiple workers, e.g. `uvicorn app.main:app --workers 4`.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
