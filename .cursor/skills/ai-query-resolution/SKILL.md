---
name: ai-query-resolution
description: >-
  Source of truth for the AI-Powered Intelligent Query Resolution System
  (FastAPI + RAG + multi-agent + React). Use when generating or editing any
  code in this repo, deciding module scope/naming/architecture, implementing
  Auth, RAG ingestion, agents, memory, analytics, dashboard, or UI, or when
  unsure what to build next.
---

# SKILL: AI-Powered Intelligent Query Resolution System

> This file is the source of truth for what we are building. Read this fully
> before generating or editing any code. When in doubt about scope, naming,
> or architecture, follow what's written here rather than guessing.

## 1. Project Overview

An AI-powered query resolution system for organizational knowledge (HR
policies, or a team's technical documentation). Users ask natural-language
questions, get answers grounded in ingested documents via RAG, with full
transparency (source chunks, confidence, citations), multi-turn memory,
and analytics that surface gaps in the knowledge base.

## 2. Core Modules (functional spec)

### Module 1 — RAG Ingestion
- Ingests HR policy docs or team technical documentation (PDF/Word/text)
- Pipeline: load → split/chunk → embed → store in vector DB
- Supports re-ingestion / updates as documents change

### Module 2 — Multi-Agent Resolution Layer
Four agents collaborate per query, coordinated by an orchestrator:
- **Query Understanding Agent** — parses intent, disambiguates the question
- **Retrieval Agent** — pulls relevant chunks from the vector DB
- **Response Generation Agent** — drafts the grounded answer via local LLM (Ollama)
- **Clarification Agent** — asks a follow-up when the query is ambiguous or under-specified

**Full response transparency is mandatory on every answer:**
- Source chunk display (which passages were used)
- Retrieval confidence score
- Citation attribution per claim in the answer

### Module 3 — Local STT / TTS (LOW PRIORITY — build last)
- Local speech-to-text and text-to-speech
- Explicitly the most complex/optional module — do not start this until 1, 2, 4, 5, 6, 7 are working

### Module 4 — Multi-Turn Conversational Memory
- Maintains context across follow-up queries and clarification exchanges within a session
- Feeds prior turns back into the Query Understanding / Retrieval agents as context

### Module 5 — Query Analytics & Knowledge Gap Detection
- Logs every query + its confidence score + whether it was answered
- Flags unanswered queries and low-confidence responses
- Detects common query themes to surface knowledge base gaps (e.g. "30 people asked about parental leave, no doc covers it")

### Module 6 — Auth
- Signup: email, name, password
- Login: validates email + password
- Issues JWT access token + refresh token
- Tokens stored client-side as **HTTP-only cookies**
- Client sends access token with each request
- On access-token expiry, refresh token silently issues a new one
- DB: `users` table (id, email, password hash, name) — name lives on `users` for now (no separate `user_details` table yet)

### Module 7 — Query History & Dashboard
- Stores per-user query history in the DB
- Dashboard surfaces: recent queries, confidence trends, personal usage — plus (from Module 5) org-wide knowledge gaps for admins

### Module 8 — UI
- React + Vite (preferred) — Streamlit acceptable for a fast v1 if needed
- Talks to backend via REST API

## 3. Actual Directory Structure (implemented)

> Prefer this layout over the aspirational `backend/` tree. The package root
> is `app/`, managed with **uv**. Do not rename to `backend/` unless asked.

```text
AI Powred Intelligent Query Resolution System/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── auth.py                 # /auth/signup|login|refresh|logout|me
│   ├── auth/
│   │   ├── cookies.py              # HTTP-only cookie set/clear
│   │   ├── dependencies.py         # get_current_user, DI helpers
│   │   ├── jwt.py                  # JWTService create/decode/verify
│   │   ├── password.py             # hash/verify (bcrypt)
│   │   └── service.py              # AuthService (signup/login/refresh)
│   ├── core/
│   │   ├── config.py               # Pydantic Settings
│   │   └── exceptions.py           # Domain exceptions
│   ├── database/
│   │   ├── connection.py           # SQLAlchemy async engine/session
│   │   └── repositories/
│   │       └── user_repository.py
│   ├── models/
│   │   └── user.py                 # User ORM
│   ├── rag/                        # Module 1 (library + CLI; no HTTP yet)
│   │   ├── config.py
│   │   ├── document_loader.py      # PDF/Word load + chunk
│   │   ├── embedding_service.py    # Ollama embeddings (mxbai-embed-large)
│   │   ├── exceptions.py
│   │   ├── ingestion.py            # IngestionPipeline
│   │   ├── retriever.py            # DocumentRetriever
│   │   └── vector_store.py         # ChromaDB (http | embedded)
│   ├── schemas/
│   │   ├── auth.py
│   │   └── rag.py
│   ├── dependencies.py
│   └── main.py                     # FastAPI entry (uvicorn app.main:app)
├── docker/
│   └── chroma-config.yaml
├── tests/
│   ├── rag/
│   │   ├── test_config.py
│   │   └── test_vector_store.py
│   └── test_auth.py
├── uploads/                        # Drop PDF/Word files for ingestion
├── docker-compose.yml              # ChromaDB on port 6334
├── .env.example
├── pyproject.toml
└── README.md
```

### Module 2 layout (LangGraph port — built)

> Agents follow the `agentic-rag-for-dummies` graph shape. Retrieval tool wraps
> existing `app.rag.retriever.DocumentRetriever` (`search_documents`), not Qdrant.

```text
app/
├── api/
│   ├── upload.py                   # Document ingestion endpoints
│   ├── query.py                    # Ask a question / reset thread
│   ├── history.py                  # (not yet)
│   └── dashboard.py                # (not yet)
├── agents/
│   ├── state.py                    # State / AgentState
│   ├── graph.py                    # main + subgraph compile
│   ├── edges.py
│   ├── nodes.py                    # rewrite, clarify, orchestrator, aggregate…
│   ├── tools.py                    # search_documents → DocumentRetriever
│   ├── prompts.py
│   ├── schemas.py                  # QueryAnalysis
│   └── execution_logger.py
├── llm/
│   └── ollama_client.py
├── transparency/
│   ├── confidence.py
│   └── citations.py
├── memory/
│   └── conversation_memory.py      # thin facade; memory lives in graph state
├── services/
│   ├── upload_service.py
│   └── query_service.py
├── ui/
│   └── gradio_app.py               # temporary Gradio (replace with React)
└── (frontend/ at repo root when Module 8 starts)
```

## 4. Implementation Status

Update this section when a module lands. Status as of last skill edit:

| Module | Status | Notes |
| --- | --- | --- |
| **6 — Auth** | **Done** | Signup/login/logout/refresh/me; JWT + HTTP-only cookies; `User` model; tests in `tests/test_auth.py` |
| **1 — RAG Ingestion** | **Done (library + HTTP)** | Load/chunk/embed/Chroma; CLI + authenticated `POST /upload` |
| **2 — Multi-Agent Resolution** | **Done (v1)** | LangGraph agents + `search_documents` tool + transparency + `POST /query` |
| **4 — Multi-turn memory** | Partial | Rolling summary + checkpointer thread in graph; facade in `app/memory` |
| **7 — Query history + dashboard** | Not started | |
| **5 — Analytics / knowledge gaps** | Not started | |
| **8 — UI** | Temp Gradio | `app/ui/gradio_app.py` — replace with React |
| **3 — STT/TTS** | Not started | Build last |

### Auth — what exists
- Routes: `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`
- Cookies: access + refresh (HTTP-only) via `CookieManager`
- Layers: `AuthService` → `UserRepository` → PostgreSQL; `JWTService`; password hash/verify
- Schemas: `SignupRequest`, `LoginRequest`, `UserPublic`, `AuthMessageResponse`, `MessageResponse`

### RAG — what exists
- Pipeline: uploads dir → extract (PDF/Word) → chunk → Ollama embed → ChromaDB
- Modes: `CHROMA_MODE=http` (Docker, port **6334**) or `embedded`
- Embedding model: `mxbai-embed-large`
- Protocols: `EmbeddingService`, `VectorStore`, `DocumentSource` (dependency inversion)

## 5. Tech Stack
- Backend: FastAPI (`app.main:app`)
- Package manager: **uv** (`uv sync`, `uv run …`)
- ORM: SQLAlchemy (async)
- DB: PostgreSQL (relational) + ChromaDB (vectors)
- Auth: JWT (access + refresh), HTTP-only cookies
- LLM / embeddings: local via Ollama
- Frontend: React + Vite (not started)

## 6. Coding Standards

Apply these to every file generated for this project, no exceptions:

- **SOLID principles**
  - *Single Responsibility*: one class/function does one thing (e.g. `jwt.py` only creates/decodes tokens — it doesn't touch the DB or cookies).
  - *Open/Closed*: prefer extension points (interfaces, strategy patterns) over editing existing logic when adding a new agent, loader type, or LLM provider.
  - *Liskov Substitution*: subclasses/implementations must be swappable without breaking callers (e.g. any `BaseAgent` subclass, any loader/protocol implementation).
  - *Interface Segregation*: small, focused interfaces/protocols instead of one giant one.
  - *Dependency Inversion*: services depend on abstractions (repository interfaces, LLM client protocol, vector store protocol), not concrete implementations — inject dependencies rather than instantiating them inline.
- **Type hints everywhere** — every function/method signature (params + return type) is fully typed. No bare `def foo(x):`. Use `Optional`, `list[str]`, `dict[str, Any]`, etc. as appropriate.
- **Dataclasses** for internal, non-API data structures (e.g. a retrieved chunk with score, internal agent state) — use `@dataclass` instead of plain dicts or ad-hoc classes.
- **Pydantic models** for anything crossing an API boundary — all request/response schemas (`app/schemas/*`) and settings/config (`app/core/config.py`) are Pydantic models, not dataclasses or raw dicts.
- **Concise code** — no boilerplate for its own sake, no speculative abstraction for things we don't need yet, no over-commented obvious code. Prefer clear, short functions over long ones; extract only when it genuinely improves readability or reuse.
- **Match existing layout** — new code goes under `app/`, not `backend/`. Follow naming already used (`jwt.py`, `service.py`, repositories package).

## 7. Build Order / Priority

Build in this order — don't jump ahead:

1. **Auth** (Module 6) — foundation everything else sits on ✅
2. **RAG Ingestion** (Module 1) — need documents in the vector store before anything can answer questions ✅ (library; upload API still open)
3. **Multi-Agent Resolution Layer** (Module 2), including transparency (source chunks, confidence, citations)
4. **Multi-turn memory** (Module 4)
5. **Query history + dashboard** (Module 7)
6. **Analytics & knowledge gap detection** (Module 5)
7. **UI** (Module 8) — can start in parallel once Auth + Query API exist
8. **STT/TTS** (Module 3) — last, only after everything above is stable

**Current build target: harden Module 2 end-to-end (Ollama + ingest + Gradio), then Module 4/7 or React UI.**

Suggested next scope (ask before expanding further):
1. End-to-end smoke: ingest via Gradio → ask → verify citations/confidence
2. Persist query history (Module 7) or extract memory facade (Module 4)
3. Replace temporary Gradio with React (Module 8)
4. Do not start STT/TTS until the above are stable

Ask before expanding scope beyond the agreed target.
