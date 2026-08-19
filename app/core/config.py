"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["ollama", "openai"]


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Development of AI-Based Knowledge Retrieval Platform with Query Resolution System"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/AI-QUERY-SYSTEM"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8501",
    ]

    # Chat LLM provider: "ollama" (local) or "openai" (GPT)
    llm_provider: LLMProvider = "ollama"
    llm_temperature: float = 0.0

    # Ollama (used when llm_provider=ollama)
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "granite4.1:8b"
    llm_seed: int = 42
    # Ollama allocates a KV cache sized to this window; lower it on low-RAM machines.
    llm_num_ctx: int = 4096

    # OpenAI GPT (used when llm_provider=openai)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # Agentic retrieval loop
    retrieval_score_threshold: float = 0.3
    default_retrieval_k: int = 5
    chunk_separator: str = "\n\n<CHUNK_BOUNDARY>\n\n"
    max_tool_calls: int = 8
    max_iterations: int = 10
    graph_recursion_limit: int = 50
    main_history_messages_to_keep: int = 4
    base_token_threshold: int = 2000
    token_growth_factor: float = 0.9

    # Agent execution logging (stdout)
    execution_logging_enabled: bool = False
    execution_log_max_chars: int = 1200
    execution_log_use_color: bool = True

    # ElevenLabs speech (STT/TTS)
    speech_enabled: bool = True
    elevenlabs_api_key: str = ""
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"
    elevenlabs_stt_realtime_model: str = "scribe_v2_realtime"
    elevenlabs_stt_realtime_audio_format: str = "pcm_16000"
    elevenlabs_stt_realtime_commit_strategy: str = "vad"
    elevenlabs_stt_realtime_vad_silence_secs: float = 1.0
    elevenlabs_tts_model: str = "eleven_flash_v2_5"
    # Premade voice (free-tier API). Voice Library IDs fail on free plans.
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    elevenlabs_tts_output_format: str = "mp3_44100_128"
    speech_max_tts_chars: int = 5000
    speech_request_timeout_seconds: float = 120.0

    # Temporary Gradio UI
    gradio_enabled: bool = True
    gradio_share: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
