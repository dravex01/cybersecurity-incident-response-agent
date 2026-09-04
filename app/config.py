from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_num_ctx: int = Field(8192, ge=2048, le=131072)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chroma_path: Path = Path("storage/chroma")
    knowledge_base_path: Path = Path("data/knowledge_base")
    chunk_size: int = Field(850, ge=200, le=5000)
    chunk_overlap: int = Field(120, ge=0, le=1000)
    top_k: int = Field(5, ge=1, le=20)
    context_threshold: float = Field(0.45, ge=0, le=1)
    max_agent_retries: int = Field(2, ge=0, le=5)
    max_rag_retries: int = Field(1, ge=0, le=3)
    enable_reranker: bool = True
    log_level: str = "INFO"
    collection_name: str = "cybersecurity_incident_response"

    @model_validator(mode="after")
    def validate_chunking(self) -> Settings:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
