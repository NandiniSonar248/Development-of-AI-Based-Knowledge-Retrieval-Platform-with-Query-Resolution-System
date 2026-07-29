# AI-Powered Intelligent Query Resolution System

## **Implemented project structure**

The structure below documents only the files and modules currently implemented in the project.

```text
AI Powred Intelligent Query Resolution System/
├── app/
│   ├── api/                  # FastAPI route handlers
│   │   └── auth.py
│   ├── auth/                 # JWT, passwords, cookies, auth service
│   ├── core/                 # App config and shared exceptions
│   ├── database/             # DB connection and repositories
│   │   └── repositories/
│   ├── models/               # ORM / domain models
│   ├── rag/                  # RAG pipeline (ingest, embed, retrieve)
│   │   ├── config.py
│   │   ├── document_loader.py
│   │   ├── embedding_service.py
│   │   ├── exceptions.py
│   │   ├── ingestion.py
│   │   ├── retriever.py
│   │   └── vector_store.py
│   ├── schemas/              # Pydantic request/response schemas
│   ├── dependencies.py
│   └── main.py               # FastAPI application entrypoint
├── docker/
│   └── chroma-config.yaml
├── tests/
│   ├── rag/
│   └── test_auth.py
├── uploads/                  # Drop PDF/Word files here for ingestion
├── docker-compose.yml        # ChromaDB HTTP server
├── .env.example
├── pyproject.toml
└── README.md
```

## Vector store

The RAG layer talks to ChromaDB in one of two modes, selected by `CHROMA_MODE`.

| Mode | Storage | Visible in the Chroma DB VS Code extension |
| --- | --- | --- |
| `http` (default) | Standalone Chroma server | Yes |
| `embedded` | Local `chromadb/` directory | No |

Use `http` when you want to browse the data with a GUI client. Start the server first:

```powershell
docker compose up -d
curl http://localhost:6334/api/v2/heartbeat
```

The server listens on port **6334** so it does not clash with other local Chroma
instances on the default 6333. Data lives in the `chroma-data` Docker volume and
survives restarts.

Relevant environment variables:

```ini
CHROMA_MODE=http
CHROMA_HOST=localhost
CHROMA_PORT=6334
```

## RAG module

Place PDF or Word files in `uploads/`. Ollama must be running with the
`mxbai-embed-large` model pulled.

### Ingestion

```powershell
ollama pull mxbai-embed-large
uv run python -m app.rag.ingestion
```

### Sample retrieval

```powershell
python -c "from app.rag.retriever import DocumentRetriever; results = DocumentRetriever().search('Short-term vs. long-term goals'); print(results)"
```

## Run the application

```powershell
uv sync
uv run python -m uvicorn app.main:app --reload
```

## Run the tests

```powershell
uv run pytest
```
