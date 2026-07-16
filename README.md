# Ledger — Agentic Financial Advisor

A reference architecture demonstrating a **multi-agent AI system with RAG**,
built as a sample Financial Advisor application. Not real financial advice —
this is an educational/demo project.

## Architecture

```
                     ┌─────────────────────────────────────┐
                     │              Orchestrator            │
                     └───────────────────┬───────────────────┘
                                          │
                 ┌────────────┬──────────┼──────────┬──────────────┐
                 ▼            ▼          ▼          ▼              │
             Planner   Portfolio Agent  Risk Agent  Recommendation  │
             (Groq)    (deterministic) (deterministic)  Agent       │
                                                      (Groq + RAG)  │
                                                          │          │
                                                          ▼          │
                                              pgvector similarity ───┘
                                              search over document
                                              chunks (fund fact sheets,
                                              risk glossary, market notes)
```

- **Planner agent** (LLM) decides which specialist agents are relevant to the
  user's question.
- **Portfolio agent** (deterministic/rule-based) computes allocation,
  concentration, and total value from the user's actual holdings — kept
  non-LLM intentionally, since numeric portfolio math should be exact.
- **Risk agent** (deterministic) compares current allocation against the
  user's stated risk tolerance and time horizon.
- **Recommendation agent** (LLM + RAG) retrieves relevant knowledge-base
  chunks via pgvector and synthesizes the final, grounded answer.
- Every step is captured in an **agent trace** returned to the frontend and
  logged/traced via OpenTelemetry, so the whole reasoning chain is auditable.
- If the LLM is unreachable (rate limit, network issue), the Planner and
  Recommendation agent both degrade gracefully — you still get the real,
  deterministic portfolio/risk numbers instead of a failed request.

## Tech stack

| Layer          | Choice                                                        |
|----------------|----------------------------------------------------------------|
| Backend        | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2                  |
| Auth           | JWT (access + refresh), bcrypt password hashing                |
| Database       | PostgreSQL 16 + pgvector                                       |
| LLM            | Groq free tier (`llama-3.1-8b-instant`) for chat/planning/recommendations |
| Embeddings     | Local, via `fastembed` (`BAAI/bge-base-en-v1.5`, ONNX, no API key/quota/billing ever) |
| RAG            | pgvector cosine similarity over chunked sample documents        |
| Logging        | structlog (JSON in prod, pretty console in dev)                 |
| Observability  | OpenTelemetry traces (Jaeger), Prometheus metrics at `/metrics` |
| Frontend       | React 18 + TypeScript + Vite + Tailwind CSS, Recharts           |
| CI/CD          | GitHub Actions (lint, test, build; Docker image build)          |
| Containers     | Docker + docker-compose (or run natively, no Docker required)   |

## Getting a free Groq API key

1. Go to https://console.groq.com/keys
2. Sign up (email or Google/GitHub) - no credit card required
3. Create a free API key
4. Put it in `backend/.env` (non-Docker) or the repo-root `.env` (Docker) as `GROQ_API_KEY`

Without this key, everything works **except** LLM-written chat commentary -
auth, portfolio, risk profile, and RAG ingestion/retrieval all work fine
without any key at all, since embeddings run locally (see below). The
Planner/Recommendation agents degrade gracefully to deterministic-only
output rather than error out when no key is set or Groq rate-limits you.

### A note on embeddings

RAG embeddings run **locally** in the backend, via
[fastembed](https://github.com/qdrant/fastembed) (`BAAI/bge-base-en-v1.5`,
ONNX runtime, no PyTorch/GPU needed) - not through an external API. This is
deliberate: this project went through several embedding-related failure
modes in a row during development (a provider deprecating its embedding
model, a billing change, an embeddings endpoint that existed in an SDK's
type hints but wasn't actually live, and a Matryoshka-resizable model whose
advertised dimension didn't match its real output in this library version),
so embeddings now use a model with a fixed, unambiguous 768-dim output and
no API key, quota, or billing dependency at all. `embed_document()`/
`embed_query()` in `app/services/llm_client.py` also double-check the real
output width at runtime and fail immediately with a clear message if it
ever drifts from `EMBEDDING_DIM`, rather than surfacing as an opaque
Postgres error.

The Docker image pre-downloads the model at build time (see
`backend/Dockerfile`), so containers never need runtime network access to
HuggingFace/GCS. In the non-Docker path, the first `python -m app.rag.ingest`
run downloads the model (~500MB) and caches it locally.

---

## Option A: Run with Docker

```bash
cp .env.example .env
# edit .env: set JWT_SECRET_KEY and GROQ_API_KEY

docker compose up --build
```

This starts:
- `postgres` (pgvector-enabled) on `5432`
- `backend` (FastAPI) on `8000`, running migrations + RAG ingestion on startup
- `frontend` (nginx serving the built React app, proxying `/api` to backend) on `80`
- `jaeger` UI on `16686` for traces
- `prometheus` on `9090` for metrics

Open http://localhost to use the app, http://localhost:8000/docs for the API
docs, http://localhost:16686 for traces, http://localhost:9090 for metrics.

## Option B: Run without Docker

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ with the [pgvector](https://github.com/pgvector/pgvector) extension installed

**Installing pgvector on Windows:** the easiest path is via
[Stack Builder](https://www.postgresql.org/download/windows/) (bundled with
the EDB Postgres installer) if pgvector is listed, or build from source using
Visual Studio's `nmake` per the
[pgvector Windows instructions](https://github.com/pgvector/pgvector#windows).
On Linux/macOS it's typically `apt install postgresql-16-pgvector` or
`brew install pgvector`.

### Quick start scripts
- Windows: `powershell -ExecutionPolicy Bypass -File scripts\run_local_windows.ps1`
- Linux/macOS: `./scripts/run_local.sh`

### Manual steps

```bash
# 1. Database
psql -U postgres -c "CREATE USER findadvisor WITH PASSWORD 'findadvisor';"
psql -U postgres -c "CREATE DATABASE findadvisor OWNER findadvisor;"
psql -U postgres -d findadvisor -c "CREATE EXTENSION vector;"
```

Note this step must run as the `postgres` superuser, not as the `findadvisor`
app user — enabling an extension requires elevated privileges. The Alembic
migration also runs `CREATE EXTENSION IF NOT EXISTS vector` defensively, but
that only succeeds because the extension already exists after the command
above; a non-superuser app account can't create it from scratch. (Docker's
`pgvector/pgvector` image sidesteps this, since its compose-created database
user is a superuser.)

```bash
# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
cp .env.example .env         # edit with your GROQ_API_KEY
alembic upgrade head
python -m app.rag.ingest
uvicorn app.main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit http://localhost:5173.

---

## Running tests

```bash
cd backend
pytest -v
```

Tests mock the Groq chat calls and the local embedding model
(`app.services.llm_client`), so they run fully offline against a real
Postgres test database — no API key or model download needed to run the
suite. 17 tests cover auth, portfolio CRUD, the deterministic portfolio/risk
agent logic, and the graceful-degradation path when the LLM is unavailable.

```bash
cd frontend
npm run lint
npm run build   # also type-checks via tsc
```

## Project layout

```
agentic-financial-advisor/
├── backend/
│   ├── app/
│   │   ├── agents/         # Planner, Portfolio, Risk, Recommendation agents + orchestrator
│   │   ├── api/v1/routes/  # auth, users, portfolio, chat, health
│   │   ├── core/           # config, security, logging, telemetry, middleware
│   │   ├── db/             # SQLAlchemy models, session
│   │   ├── rag/            # retriever + ingestion script
│   │   ├── schemas/        # Pydantic request/response models
│   │   └── services/       # Groq chat client + local embedding wrapper
│   ├── alembic/            # DB migrations
│   ├── sample_docs/        # Synthetic RAG knowledge base (swap in real docs here)
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/            # typed API client + endpoints
│   │   ├── components/     # Sidebar, AgentTraceLedger, charts, etc.
│   │   ├── context/        # AuthContext
│   │   └── pages/          # Login, Register, Dashboard, Portfolio, Advisor, Risk
│   └── Dockerfile
├── observability/          # Prometheus scrape config
├── db/init/                # First-run SQL (enables pgvector on fresh Docker volumes)
├── scripts/                # run_local.sh / run_local_windows.ps1
├── .github/workflows/ci.yml
└── docker-compose.yml
```

## Swapping in real RAG documents

Drop `.md` files into `backend/sample_docs/`, with a `category: <name>` first
line, then re-run `python -m app.rag.ingest`. The ingestion script chunks by
paragraph and embeds each chunk locally via fastembed - no external API call.

## Extending the agent roster

Add a new agent in `backend/app/agents/`, register it in
`app/agents/orchestrator.py`'s `_AGENT_REGISTRY`, and update the Planner's
system prompt (`app/agents/planner.py`) to describe when it should run.

## Pushing this to GitHub

See `GITHUB_SETUP.md` for the exact commands.
