"""RAG configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RAGConfig:
    """Central configuration for embedding, storage, and retrieval."""

    embedding_model: str = "mxbai-embed-large"
    ollama_base_url: str = "http://localhost:11434"
    collection_name: str = "documents"
    persist_dir: Path = PROJECT_ROOT / "chromadb"
    uploads_dir: Path = PROJECT_ROOT / "uploads"
    default_top_k: int = 5

