# AGENTS.md

Compact guide for OpenCode sessions working in this repo. Read before editing code.

## Toolchain

- Package manager is **uv** (not pip/poetry). Always run via `uv run ...`; do not call `python`/`pytest` directly or you'll bypass the venv in `.venv/`.
- Python **3.11** (pinned in `.python-version`). `requires-python = ">=3.11"`.
- No lint/typecheck/format command is configured in `pyproject.toml` — do not invent one. `ruff` caches exist (`.ruff_cache/`) but no config is checked in; ask before running it.
- Tests: `uv run pytest`. Single test: `uv run pytest tests/agent/test_tools.py::test_search_documents_filters_low_scores`. One package: `uv run pytest tests/agent`.
- pytest is configured in `pyproject.toml`: `asyncio_mode = "auto"`, `testpaths = ["tests"]`, `pythonpath = ["."]`. Async tests need no marker.
- Test layout mirrors `app/`: `tests/agent/` (graph, tools, edges, transparency), `tests/rag/` (vector store, config), `tests/test_auth.py`, `tests/test_llm_factory.py`.

## Running the app

- API: `uv run python -m uvicorn app.main:app --reload` (or `uv run python main.py`, which hardcodes port 8000 + reload).
- Gradio UI: `uv run python -m app.ui.gradio_app` → http://localhost:7860. Temporary; Module 8 (React) replaces it. The launch reads `GRADIO_ENABLED`/`GRADIO_SHARE` from settings only if invoked through the app lifespan — the `__main__` entry calls `launch_gradio()` directly.
- RAG ingest (CLI, no HTTP): `uv run python -m app.rag.ingestion` after dropping PDF/Word files in `uploads/`.

## External services — must be running before query/ingest

- **Ollama** with two models pulled: `mxbai-embed-large` (embeddings, always local) and `granite4.1:8b` (default chat model when `LLM_PROVIDER=ollama`). Pull with `ollama pull <model>`.
- **ChromaDB** in one of two modes via `CHROMA_MODE`:
  - `http` (default per README): `docker compose up -d` → Chroma on port **6334** (not 6333; chosen to avoid local clashes). Healthcheck: `curl http://localhost:6334/api/v2/heartbeat`.
  - `embedded` (default per `.env.example`): writes to `chromadb/` on disk. Not visible to the Chroma VS Code extension.
  - Note: README says `http` is default but `.env.example` ships `CHROMA_MODE=embedded`. Trust `.env.example` for fresh setups; the README documents the `http` path.
- **PostgreSQL** reachable at `DATABASE_URL` (async SQLAlchemy + asyncpg). App calls `init_db()` on lifespan startup, so the DB must be up or startup fails. Query-service warm-up on startup is best-effort (wrapped in try/except, only printed when `DEBUG=true`). Auth tests mock the DB; query/ingest do not need it.

## Configuration

- All settings in `app/core/config.py` (`Settings`, pydantic-settings), loaded from `.env` (copy `.env.example`). `get_settings()` is `@lru_cache` — **restart the API/Gradio after changing `.env`**; runtime tweaks will not take effect.
- LLM provider switch: `LLM_PROVIDER=ollama|openai`. OpenAI needs `OPENAI_API_KEY` (factory raises `LLMConfigError` if empty). Embeddings **always** go through Ollama regardless of chat provider.
- Agentic guardrails (`MAX_ITERATIONS`, `MAX_TOOL_CALLS`, `GRAPH_RECURSION_LIMIT`, `RETRIEVAL_SCORE_THRESHOLD`, `DEFAULT_RETRIEVAL_K`, `BASE_TOKEN_THRESHOLD`, `TOKEN_GROWTH_FACTOR`) are all env-driven — change there, not in code.

## Architecture — non-obvious facts

- Package root is **`app/`**, not `backend/`. Do not rename; the `.cursor` skill explicitly forbids it.
- Entry point: `app/main.py` builds the FastAPI app via `create_app()`; `main.py` at repo root is a thin `uvicorn.run` wrapper. Routers: `auth`, `upload`, `query` (all mounted in `app/main.py`). Health check at `GET /health`.
- Auth uses JWT access + refresh tokens in **HTTP-only cookies** (not Authorization headers). Endpoints under `/auth/*`, plus `POST /upload` and `POST /query` require the cookie. `app/dependencies.py` re-exports `get_current_user`, `get_db`, `get_query_service`.
- The agent layer is a **two-level LangGraph** (main graph + agent subgraph). The orchestrator LLM **never** touches Chroma directly; it calls the `search_documents` tool → `DocumentRetriever` → `ChromaVectorStore`. Do not wire Qdrant or parent-child chunking — this is a hard constraint in both the README and the `.cursor` skill.
- Main graph can **pause** at `request_clarification` (`interrupt_before`) and resume on user reply — the UI/API must support this resume flow, not just fire-and-forget.
- Memory lives in **graph state** (rolling summary + LangGraph checkpointer per thread). `app/memory/conversation_memory.py` is a thin facade — don't move memory out of state.
- Transparency (`app/transparency/`: citations + confidence) is **mandatory on every answer** per the skill; don't ship a query path that skips it.
- `app/agents/agent_execution_flow.drawio` is a diagram, not code — do not edit by hand unless asked.

## Coding standards (from `.cursor/skills/ai-query-resolution/SKILL.md`)

- **Type hints everywhere** on every signature (params + return). No bare `def foo(x):`.
- Pydantic models for anything crossing an API boundary (`app/schemas/*`, `app/core/config.py`). Dataclasses for internal non-API structures (e.g. retrieved chunks).
- SOLID + dependency injection: services depend on protocols (`EmbeddingService`, `VectorStore`, `DocumentSource`, LLM client), not concrete classes. Inject, don't instantiate inline.
- Liskov: any loader/protocol/agent impl must be swappable without breaking callers.
- Concise code: no speculative abstraction, no boilerplate-for-its-own-sake, no over-commenting obvious code. Do not add comments unless asked.
- New code goes under `app/` following existing naming (`jwt.py`, `service.py`, repositories package).

## Build order (don't jump ahead)

Per the skill: Auth ✅ → RAG ✅ → Multi-Agent (current hardening target) → Multi-turn memory → Query history/dashboard → Analytics → React UI → STT/TTS (last). **Do not start STT/TTS (Module 3) until 1,2,4,5,6,7 are stable.** Ask before expanding scope beyond the agreed target.

## Things to ignore / not commit

- `.gitignore` excludes `.env`, `chromadb/`, `uploads/`, `.cursor/` — never stage these.
- `_repro_warn.py`, `_repro_warn2.py`, `_repro_warn3.py` at repo root are scratch repro scripts, not part of the app.
- `chromadb/` and `uploads/` are runtime artifacts (embedded store + dropped docs).

## Reference docs in repo

- `README.md` — architecture deep-dive (Mermaid diagrams, node table, guardrail table). Trust it for the agent graph; trust `.env.example` + `pyproject.toml` + `app/core/config.py` for exact config.
- `.cursor/skills/ai-query-resolution/SKILL.md` — source of truth for module scope, naming, build order, and coding standards. Read fully before architectural changes.
